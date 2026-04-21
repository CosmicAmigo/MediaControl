using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using System.Windows.Shell;
using Windows.Media.Control;
using System.Linq;

namespace MediaControlApp
{
    public partial class MainWindow : Window
    {
        private TextBlock titleText, artistText, sourceText;
        private Slider volumeSlider;
        private Window triggerWindow;
        private DispatcherTimer timer;

        public MainWindow()
        {
            InitializeComponent();
            SetupStyles();
            BuildUI();
            SetupTaskbarThumbnails();
            SetupSemicircleTrigger();
            
            this.Topmost = true;
            this.ShowInTaskbar = true; // Enabled for the hover preview feature
            this.Visibility = Visibility.Collapsed;
            
            timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            timer.Tick += UpdateMediaInfo;
            timer.Start();
        }

        private void SetupStyles()
        {
            this.Width = 320; this.Height = 180;
            this.WindowStyle = WindowStyle.None;
            this.AllowsTransparency = true;
            this.Background = Brushes.Transparent;
        }

        private void BuildUI()
        {
            var border = new Border {
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#121212")),
                CornerRadius = new CornerRadius(15),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#333333")),
                BorderThickness = new Thickness(1.5),
                Padding = new Thickness(15)
            };

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(45) });

            // Left Side: Media Info
            var infoStack = new StackPanel();
            sourceText = new TextBlock { Text = "APP.EXE", Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1DB954")), FontSize = 10, FontWeight = FontWeights.Bold };
            titleText = new TextBlock { Text = "Track Title", Foreground = Brushes.White, FontSize = 16, FontWeight = FontWeights.Bold, TextTrimming = TextTrimming.CharacterEllipsis };
            artistText = new TextBlock { Text = "Artist - Album", Foreground = Brushes.Gray, FontSize = 12 };
            
            var controls = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 15, 0, 0) };
            controls.Children.Add(CreateMediaBtn("⏮", 35, (s, e) => MediaAction("prev")));
            controls.Children.Add(CreateMediaBtn("⏯", 50, (s, e) => MediaAction("play"), "#1DB954"));
            controls.Children.Add(CreateMediaBtn("⏭", 35, (s, e) => MediaAction("next")));

            infoStack.Children.Add(sourceText);
            infoStack.Children.Add(titleText);
            infoStack.Children.Add(artistText);
            infoStack.Children.Add(controls);
            Grid.SetColumn(infoStack, 0);

            // Right Side: Volume Slider
            volumeSlider = new Slider {
                Orientation = Orientation.Vertical, Minimum = 0, Maximum = 100, Value = 50,
                Height = 120, Foreground = Brushes.Gray
            };
            Grid.SetColumn(volumeSlider, 1);

            grid.Children.Add(infoStack);
            grid.Children.Add(volumeSlider);
            border.Child = grid;
            this.Content = border;
        }

        private void SetupTaskbarThumbnails()
        {
            TaskbarItemInfo = new TaskbarItemInfo();
            var playThumb = new ThumbButtonInfo { Description = "Play/Pause", Symbol = "\uE768" };
            playThumb.Click += (s, e) => MediaAction("play");
            
            var nextThumb = new ThumbButtonInfo { Description = "Next", Symbol = "\uE761" };
            nextThumb.Click += (s, e) => MediaAction("next");

            TaskbarItemInfo.ThumbButtonInfos.Add(playThumb);
            TaskbarItemInfo.ThumbButtonInfos.Add(nextThumb);
        }

        private void SetupSemicircleTrigger()
        {
            triggerWindow = new Window {
                Width = 20, Height = 40, WindowStyle = WindowStyle.None, AllowsTransparency = true,
                Background = Brushes.Transparent, Topmost = true, ShowInTaskbar = false
            };
            var arc = new Border {
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1DB954")),
                CornerRadius = new CornerRadius(20, 0, 0, 20), Width = 20, Height = 40
            };
            triggerWindow.Content = arc;
            triggerWindow.Left = SystemParameters.PrimaryScreenWidth - 20;
            triggerWindow.Top = SystemParameters.PrimaryScreenHeight / 2 - 20;
            
            triggerWindow.MouseEnter += (s, e) => {
                this.Left = SystemParameters.PrimaryScreenWidth - 340;
                this.Top = SystemParameters.PrimaryScreenHeight / 2 - 90;
                this.Visibility = Visibility.Visible;
            };
            this.MouseLeave += (s, e) => this.Visibility = Visibility.Collapsed;
            triggerWindow.Show();
        }

        private async void UpdateMediaInfo(object sender, EventArgs e)
        {
            try {
                var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
                var session = manager.GetCurrentSession();
                if (session != null) {
                    var props = await session.TryGetMediaPropertiesAsync();
                    titleText.Text = props.Title;
                    artistText.Text = $"{props.Artist} - {props.AlbumTitle}";
                    sourceText.Text = "• " + session.SourceAppUserModelId.Split('!')[0].Split('\\').Last().ToUpper();
                }
            } catch { }
        }

        private async void MediaAction(string type)
        {
            var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
            var session = manager.GetCurrentSession();
            if (session == null) return;
            if (type == "play") await session.TryTogglePlayPauseAsync();
            if (type == "next") await session.TrySkipNextAsync();
            if (type == "prev") await session.TrySkipPreviousAsync();
        }

        private Button CreateMediaBtn(string icon, double w, RoutedEventHandler click, string bg = "Transparent") => new Button {
            Content = icon, Width = w, Height = 35, Margin = new Thickness(5, 0, 5, 0),
            Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bg)),
            BorderThickness = new Thickness(0)
        };
    }
}
