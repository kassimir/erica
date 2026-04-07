using Erica.Shell.Config;
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
        var startup = ShellStartupOptions.Parse(Environment.GetCommandLineArgs());
        ShellAppHost.Initialize(startup);
        _window = new MainWindow();
        _window.Activate();
    }
}
