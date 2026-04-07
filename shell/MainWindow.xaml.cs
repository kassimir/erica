using Erica.Shell.Services;
using Microsoft.UI;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Windows.System;
using WinRT.Interop;

namespace Erica.Shell;

public sealed partial class MainWindow : Window
{
    private bool _quakeVisible;
    private bool _paletteVisible;

    public MainWindow()
    {
        InitializeComponent();
        Title = "Erica";
        ExtendsContentIntoTitleBar = true;

        var hwnd = WindowNative.GetWindowHandle(this);
        var windowId = Win32Interop.GetWindowIdFromWindow(hwnd);
        var appWindow = AppWindow.GetFromWindowId(windowId);
        appWindow.SetPresenter(AppWindowPresenterKind.FullScreen);

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
            await ShellAppHost.Voice.TranscribePlaceholderAsync();
            StatusLeft.Text = "Voice: see status / logs";
        };
        RootGrid.KeyboardAccelerators.Add(voiceAccel);

        var sendAccel = new KeyboardAccelerator { Key = VirtualKey.F5 };
        sendAccel.Invoked += async (_, e) =>
        {
            e.Handled = true;
            if (_quakeVisible)
                await QuakeSendAsync();
        };
        RootGrid.KeyboardAccelerators.Add(sendAccel);
    }

    private void TogglePalette()
    {
        _paletteVisible = !_paletteVisible;
        PaletteOverlay.Visibility = _paletteVisible ? Visibility.Visible : Visibility.Collapsed;
        if (_paletteVisible)
        {
            PaletteInput.Focus(FocusState.Programmatic);
            StatusLeft.Text = "Command palette";
        }
        else
        {
            StatusLeft.Text = "Ready";
        }
    }

    private void ToggleQuake()
    {
        _quakeVisible = !_quakeVisible;
        QuakeRow.Height = _quakeVisible ? new GridLength(280) : new GridLength(0);
        if (_quakeVisible)
        {
            QuakeInput.Focus(FocusState.Programmatic);
            StatusLeft.Text = "Console";
        }
        else
        {
            StatusLeft.Text = "Ready";
        }
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
            StatusLeft.Text = "Sending…";
            var result = await ShellAppHost.Router.RouteAsync(text, streamToAgent: false);
            var tag = result.Target == CommandTarget.CopilotChat ? "copilot" : "agent";
            if (!string.IsNullOrEmpty(result.Output))
                QuakeOutput.Text += $"[{tag}]\n{result.Output}\n";
            StatusLeft.Text = "OK";
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Error("Palette command failed", ex);
            StatusLeft.Text = "Error";
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
            StatusLeft.Text = "Streaming…";
            var result = await ShellAppHost.Router.RouteAsync(text, streamToAgent: true);
            QuakeOutput.Text += result.Output + "\n";
            StatusLeft.Text = "Done";
        }
        catch (Exception ex)
        {
            ShellAppHost.Log.Error("Quake stream failed", ex);
            QuakeOutput.Text += ex.Message + "\n";
            StatusLeft.Text = "Error";
        }
    }
}
