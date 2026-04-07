using Microsoft.UI.Xaml;

namespace Erica.Shell;

public partial class App : Application
{
    private Window? _window;

    public App()
    {
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        ShellAppHost.Initialize();
        _window = new MainWindow();
        _window.Activate();
    }
}
