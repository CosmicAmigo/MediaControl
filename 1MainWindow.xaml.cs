using System;
using System.IO;
using System.Windows;
using System.Windows.Media.Imaging;
using Windows.Media.Control;
using Windows.Storage.Streams;

namespace MediaControlApp {
    public partial class MainWindow : Window {
        private GlobalSystemMediaTransportControlsSessionManager? _manager;

        public MainWindow() {
            InitializeComponent();
            InitializeMedia();
        }

        private async void InitializeMedia() {
            _manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
            UpdateUI();
            
            // Poll for changes every 2 seconds
            var timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(2) };
            timer.Tick += (s, e) => UpdateUI();
            timer.Start();
        }

        private async void UpdateUI() {
            var session = _manager?.GetCurrentSession();
            if (session == null) return;

            var props = await session.TryGetMediaPropertiesAsync();
            TitleLabel.Text = props.Title;
            ArtistLabel.Text = props.Artist;
            SourceLabel.Text = "• " + session.SourceAppUserModelId.Split('!')[0].ToUpper();

            // Load Album Art
            if (props.Thumbnail != null) {
                using (IRandomAccessStreamWithContentType stream = await props.Thumbnail.OpenReadAsync()) {
                    var bitmap = new BitmapImage();
                    bitmap.BeginInit();
                    bitmap.StreamSource = stream.AsStream();
                    bitmap.CacheOption = BitmapCacheOption.OnLoad;
                    bitmap.EndInit();
                    AlbumArt.Source = bitmap;
                }
            }
        }

        // Trigger logic
        private void Window_MouseLeave(object sender, System.Windows.Input.MouseEventArgs e) {
            this.Visibility = Visibility.Collapsed;
        }

        private void Play_Click(object sender, RoutedEventArgs e) => _manager?.GetCurrentSession()?.TryTogglePlayPauseAsync();
        private void Next_Click(object sender, RoutedEventArgs e) => _manager?.GetCurrentSession()?.TrySkipNextAsync();
        private void Prev_Click(object sender, RoutedEventArgs e) => _manager?.GetCurrentSession()?.TrySkipPreviousAsync();
        
        private void VolSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e) {
            // Volume logic here
        }
    }
}
