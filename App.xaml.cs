using System.Windows;

namespace MediaControlApp
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // Setup a global error handler so the app doesn't crash 
            // if the Windows Media Session is busy or interrupted.
            this.DispatcherUnhandledException += (s, args) =>
            {
                // We mark it as handled so the app stays alive
                args.Handled = true;
                System.Diagnostics.Debug.WriteLine($"Caught error: {args.Exception.Message}");
            };
        }
    }
}
