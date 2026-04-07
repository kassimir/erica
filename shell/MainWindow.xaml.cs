using System;
using System.Threading.Tasks;
using Erica.Shell.Services;
using Microsoft.UI;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media.Animation;
using Windows.System;
using WinRT.Interop;

namespace Erica.Shell;

public sealed partial class MainWindow : Window
{
    private const double QuakeHeight = 280;

    private bool _paletteVisible;
    private bool _quakeOpen;
    private bool _quakeAnimating;
    private DispatcherQueueTimer? _healthTimer;

    public MainWindow()
    {
        InitializeComponent();
        Title = "Erica";
        ExtendsContentIntoTitleBar = true;

        var hwnd = WindowNative.GetWindowHandle(this);
        var windowId = Win32Interop.GetWindowIdFromWindow(hwnd);
        var appWindow = AppWindow.GetFromWindowId(windowId);
        appWindow.SetPresenter(AppWindowPresenterKind.FullScreen);

        Loaded += MainWindow_Loaded;

        var paletteAccel = new KeyboardAccelerator
        {
            Key = VirtualKey.Space,
            Modifiers = VirtualKeyModifiers.Control,
        };
        paletteAccel.Invoked += (_, e) =>
        {
            e.Handled = true;
            TogglePalette();
        };
        RootGrid.KeyboardAccelerators.Add(paletteAccel);

        var quakeAccel = new KeyboardAccelerator
        {
            Key = VirtualKey.Oem3,
            Modifiers = VirtualKeyModifiers.Control,
        };
        quakeAccel.Invoked += (_, e) =>
        {
            e.Handled = true;
            ToggleQuake();
        };
        RootGrid.KeyboardAccelerators.Add(quakeAccel);

        var voiceAccel = new KeyboardAccelerator
        {
            Key = VirtualKey.V,
            Modifiers = VirtualKeyModifiers.Control | VirtualKeyModifiers.Shift,
        };
        voiceAccel.Invoked += async (_, e) =>
        {
            e.Handled = true;
            StatusActivity.Text = "Voice: placeholder (wire capture + /voice/stt)";
            await ShellAppHost.Voice.TranscribePlaceholderAsync();
            ShellAppHost.Log.Information("Push-to-talk: stub");
        };
        RootGrid.KeyboardAccelerators.Add(voiceAccel);

        var sendAccel = new KeyboardAccelerator { Key = VirtualKey.F5 };
        sendAccel.Invoked += async (_, e) =>
        {
            e.Handled = true;
            if (_quakeOpen)
                await QuakeSendAsync();
        };
        RootGrid.KeyboardAccelerators.Add(sendAccel);
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        _ = RefreshHealthAsync();
        var dq = DispatcherQueue.GetForCurrentThread();
        _healthTimer = dq.CreateTimer();
        _healthTimer.Interval = TimeSpan.FromSeconds(20);
        _healthTimer.Tick += (_, _) => _ = RefreshHealthAsync();
        _healthTimer.Start();
    }

    private async Task RefreshHealthAsync()
    {
        try
        {
            var h = await ShellAppHost.Agent.GetHealthAsync();
            if (h == null)
            {
                StatusConnection.Text = "Agent: offline";
                StatusMode.Text = "Mode: —";
                return;
            }

            if (h.Ok)
            {
                var authority = AgentAuthority(ShellAppHost.Settings.AgentBaseUrl);
                StatusConnection.Text = $"Agent: online · {authority}";
                StatusMode.Text = string.IsNullOrWhiteSpace(h.Mode) ? "Mode: —" : $"Mode: {h.Mode}";
            }
            else
            {
                StatusConnection.Text = "Agent: unreachable";
                StatusMode.Text = "Mode: —";
            }
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Warning($"Health refresh: {ex.Message}");
            StatusConnection.Text = "Agent: offline";
            StatusMode.Text = "Mode: —";
        }
    }

    private static string AgentAuthority(string baseUrl)
    {
        try
        {
            var u = new Uri(baseUrl.Trim());
            return u.Authority;
        }
        catch
        {
            return baseUrl;
        }
    }

    private void TogglePalette()
    {
        _paletteVisible = !_paletteVisible;
        PaletteOverlay.Visibility = _paletteVisible ? Visibility.Visible : Visibility.Collapsed;
        if (_paletteVisible)
        {
            PaletteInput.Focus(FocusState.Programmatic);
            StatusActivity.Text = "Command palette";
        }
        else
        {
            StatusActivity.Text = "";
        }
    }

    private void ToggleQuake()
    {
        if (_quakeAnimating)
            return;
        _quakeOpen = !_quakeOpen;
        AnimateQuakeSlide(_quakeOpen);
    }

    private void AnimateQuakeSlide(bool open)
    {
        _quakeAnimating = true;
        var from = QuakeTransform.TranslateY;
        var to = open ? 0 : -QuakeHeight;
        var anim = new DoubleAnimation
        {
            From = from,
            To = to,
            Duration = new Duration(TimeSpan.FromMilliseconds(220)),
            EnableDependentAnimation = true,
        };
        Storyboard.SetTarget(anim, QuakeTransform);
        Storyboard.SetTargetProperty(anim, "TranslateY");
        var sb = new Storyboard();
        sb.Children.Add(anim);
        sb.Completed += (_, _) =>
        {
            _quakeAnimating = false;
            QuakeSlide.IsHitTestVisible = open;
            QuakeTransform.TranslateY = to;
            if (open)
            {
                QuakeInput.Focus(FocusState.Programmatic);
                StatusActivity.Text = "Console (stream)";
            }
            else
            {
                StatusActivity.Text = "";
            }
        };
        sb.Begin();
    }

    private async void PaletteInput_KeyDown(object sender, KeyRoutedEventArgs e)
    {
        if (e.Key == VirtualKey.Escape)
        {
            if (_paletteVisible)
                TogglePalette();
            return;
        }

        if (e.Key != VirtualKey.Enter)
            return;

        var text = PaletteInput.Text?.Trim() ?? "";
        if (string.IsNullOrEmpty(text))
            return;

        await SendPaletteAsync(text);
        PaletteInput.Text = "";
        if (_paletteVisible)
            TogglePalette();
    }

    private async Task SendPaletteAsync(string text)
    {
        try
        {
            StatusActivity.Text = "POST /execute…";
            var result = await ShellAppHost.Router.RouteAsync(text, streamToAgent: false);
            var tag = result.Target == CommandTarget.CopilotChat ? "copilot" : "agent";
            if (!string.IsNullOrEmpty(result.Output))
                QuakeOutput.Text += $"[{tag}]\n{result.Output}\n";
            StatusActivity.Text = "Done";
            await RefreshHealthAsync();
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Error("Palette command failed", ex);
            StatusActivity.Text = $"Error: {ex.Message}";
            QuakeOutput.Text += ex.Message + "\n";
        }
    }

    private async void QuakeSend_Click(object sender, RoutedEventArgs e)
    {
        await QuakeSendAsync();
    }

    private async Task QuakeSendAsync()
    {
        var text = QuakeInput.Text?.Trim() ?? "";
        if (string.IsNullOrEmpty(text))
            return;
        QuakeInput.Text = "";
        await SendQuakeStreamAsync(text);
    }

    private async Task SendQuakeStreamAsync(string text)
    {
        try
        {
            StatusActivity.Text = "POST /execute/stream…";
            var result = await ShellAppHost.Router.RouteAsync(text, streamToAgent: true);
            QuakeOutput.Text += result.Output + "\n";
            StatusActivity.Text = "Done";
            await RefreshHealthAsync();
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Error("Quake stream failed", ex);
            QuakeOutput.Text += ex.Message + "\n";
            StatusActivity.Text = $"Error: {ex.Message}";
        }
    }
}
