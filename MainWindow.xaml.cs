using System;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Media.Imaging;
using Windows.Media.Control;
using Windows.Storage.Streams;

namespace MediaControlApp
{
    public partial class MainWindow : Window
    {
        private GlobalSystemMediaTransportControlsSessionManager? _manager;

        public MainWindow()
        {
            InitializeComponent();
            InitializeMedia();
            
            // This hides the main window from the Alt-Tab menu but keeps the Taskbar Icon
            this.ShowInTaskbar = true; 
        }

        private async void InitializeMedia()
        {
            _manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
            UpdateUI();

            var timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(1.5) };
            timer.Tick += (s, e) => UpdateUI();
            timer.Start();
        }

        private async void UpdateUI()
        {
            try {
                var session = _manager?.GetCurrentSession();
                if (session == null) return;

                var props = await session.TryGetMediaPropertiesAsync();
                TitleLabel.Text = props.Title ?? "Unknown Title";
                ArtistLabel.Text = $"{props.Artist} - {props.AlbumTitle}";
                
                // Get clean App Name for the label
                var rawId = session.SourceAppUserModelId.Split('!')[0];
                SourceLabel.Text = "• " + Path.GetFileNameWithoutExtension(rawId).ToUpper();

                // 1. Load Album Art
                if (props.Thumbnail != null) {
                    using (var stream = await props.Thumbnail.OpenReadAsync()) {
                        var bitmap = new BitmapImage();
                        bitmap.BeginInit();
                        bitmap.StreamSource = stream.AsStream();
                        bitmap.CacheOption = BitmapCacheOption.OnLoad;
                        bitmap.EndInit();
                        AlbumArt.Source = bitmap;
                    }
                }

                // 2. Load App Icon (Extracts from the playing process)
                try {
                    var process = System.Diagnostics.Process.GetProcessesByName(Path.GetFileNameWithoutExtension(rawId)).FirstOrDefault();
                    if (process != null) {
                        var icon = System.Drawing.Icon.ExtractAssociatedIcon(process.MainModule.FileName);
                        AppIcon.Source = System.Windows.Interop.Imaging.CreateBitmapSourceFromHIcon(
                            icon.Handle, Int32Rect.Empty, BitmapSizeOptions.FromEmptyOptions());
                    }
                } catch { /* Fallback if icon fetch fails */ }

            } catch { }
        }

        // Media Controls
        private void Play_Click(object sender, RoutedEventArgs e) => _manager?.GetCurrentSession()?.TryTogglePlayPauseAsync();
        private void Next_Click(object sender, RoutedEventArgs e) => _manager?.GetCurrentSession()?.TrySkipNextAsync();
        private void Prev_Click(object sender, RoutedEventArgs e) => _manager?.GetCurrentSession()?.TrySkipPreviousAsync();
        
        private void Window_MouseLeave(object sender, System.Windows.Input.MouseEventArgs e) => this.Visibility = Visibility.Collapsed;
    }
}
