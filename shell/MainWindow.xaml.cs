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
using Windows.Graphics;
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
    private GlobalHotkeyService? _hotkeys;
    private readonly DispatcherQueue _dq;

    public MainWindow()
    {
        _dq = DispatcherQueue.GetForCurrentThread();
        InitializeComponent();
        Title = "Erica";
        ExtendsContentIntoTitleBar = true;

        ApplyWindowPresenter();

        var hwnd = WindowNative.GetWindowHandle(this);

        Loaded += MainWindow_Loaded;
        Closed += MainWindow_Closed;

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
            await VoiceHotkeyAsync();
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

        try
        {
            _hotkeys = new GlobalHotkeyService(hwnd, _dq, OnGlobalHotkey);
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Warning($"Global hotkeys unavailable (use in-window shortcuts): {ex.Message}");
        }
    }

    private void ApplyWindowPresenter()
    {
        var hwnd = WindowNative.GetWindowHandle(this);
        var windowId = Win32Interop.GetWindowIdFromWindow(hwnd);
        var appWindow = AppWindow.GetFromWindowId(windowId);
        var mode = ShellAppHost.Settings.WindowMode?.Trim() ?? "FullScreen";

        if (string.Equals(mode, "Windowed", StringComparison.OrdinalIgnoreCase))
        {
            appWindow.SetPresenter(AppWindowPresenterKind.Default);
            if (appWindow.Presenter is OverlappedPresenter op)
                op.SetBorderAndTitleBar(false, false);
            appWindow.Resize(new SizeInt32(1400, 900));
            ChromeRowDefinition.Height = new GridLength(32);
            WindowChromeBar.Visibility = Visibility.Visible;
            ExtendsContentIntoTitleBar = true;
            SetTitleBar(TitleBarDragRegion);
        }
        else
        {
            appWindow.SetPresenter(AppWindowPresenterKind.FullScreen);
        }
    }

    private void MainWindow_Closed(object sender, WindowEventArgs args)
    {
        _hotkeys?.Dispose();
        _hotkeys = null;
    }

    private void ExitWindowChrome_Click(object sender, RoutedEventArgs e)
    {
        Application.Current.Exit();
    }

    private void OnGlobalHotkey(int id)
    {
        switch (id)
        {
            case GlobalHotkeyService.IdPalette:
                TogglePalette();
                break;
            case GlobalHotkeyService.IdQuake:
                ToggleQuake();
                break;
            case GlobalHotkeyService.IdVoice:
                _ = VoiceHotkeyAsync();
                break;
        }
    }

    private async Task VoiceHotkeyAsync()
    {
        StatusActivity.Text = "Voice: placeholder (wire capture + /voice/stt)";
        await ShellAppHost.Voice.TranscribePlaceholderAsync();
        ShellAppHost.Log.Information("Push-to-talk: stub");
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        _ = RefreshHealthAsync();
        _healthTimer = _dq.CreateTimer();
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
                SetError("Reconnecting… check agent or URL.");
                return;
            }

            if (h.Ok)
            {
                var authority = AgentAuthority(ShellAppHost.Settings.AgentBaseUrl);
                StatusConnection.Text = $"Agent: online · {authority}";
                StatusMode.Text = string.IsNullOrWhiteSpace(h.Mode) ? "Mode: —" : $"Mode: {h.Mode}";
                ClearError();
            }
            else
            {
                StatusConnection.Text = "Agent: unreachable";
                StatusMode.Text = "Mode: —";
                SetError("HTTP error from /health.");
            }
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Warning($"Health refresh: {ex.Message}");
            StatusConnection.Text = "Agent: offline";
            StatusMode.Text = "Mode: —";
            SetError(ex.Message);
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

    private void SetError(string message)
    {
        StatusError.Text = message;
    }

    private void ClearError()
    {
        StatusError.Text = "";
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
            ClearError();
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
            SetError(ex.Message);
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
            ClearError();
            StatusActivity.Text = "POST /execute/stream…";
            var progress = new Progress<string>(line =>
            {
                _dq.TryEnqueue(() =>
                {
                    QuakeOutput.Text += line + "\n";
                    QuakeScrollViewer.ChangeView(null, float.MaxValue, null);
                });
            });
            var result = await ShellAppHost.Router.RouteAsync(text, streamToAgent: true, streamChunk: progress);
            if (!string.IsNullOrEmpty(result.Output))
            {
                _dq.TryEnqueue(() =>
                {
                    QuakeOutput.Text += result.Output + "\n";
                    QuakeScrollViewer.ChangeView(null, float.MaxValue, null);
                });
            }

            StatusActivity.Text = "Done";
            await RefreshHealthAsync();
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Error("Quake stream failed", ex);
            SetError(ex.Message);
            QuakeOutput.Text += ex.Message + "\n";
            StatusActivity.Text = $"Error: {ex.Message}";
        }
    }
}
