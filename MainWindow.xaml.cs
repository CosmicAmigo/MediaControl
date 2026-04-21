using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using System.Runtime.InteropServices;
using Windows.Media.Control;
using System.Linq;

namespace MediaControlApp
{
    public partial class MainWindow : Window
    {
        // UI Elements
        private TextBlock titleLabel, artistLabel, sourceLabel;
        private Button playBtn, shufBtn, repBtn;
        private Window triggerWindow;
        private DispatcherTimer updateTimer;

        public MainWindow()
        {
            InitializeComponent();
            SetupUI();
            SetupTrigger();
            StartMediaPolling();
            
            // Hide from Taskbar & Start hidden
            this.ShowInTaskbar = false;
            this.Topmost = true;
            this.Visibility = Visibility.Collapsed;
        }

        private void SetupUI()
        {
            this.Width = 240; this.Height = 150;
            this.Background = Brushes.Transparent;
            this.WindowStyle = WindowStyle.None;
            this.AllowsTransparency = true;

            var mainFrame = new Border {
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#121212")),
                CornerRadius = new CornerRadius(12),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#333333")),
                BorderThickness = new Thickness(1)
            };

            var stack = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            
            sourceLabel = new TextBlock { Text = "SOURCE", Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1DB954")), FontSize = 10, FontWeight = FontWeights.Bold, HorizontalAlignment = HorizontalAlignment.Center, Margin = new Thickness(0,10,0,0) };
            titleLabel = new TextBlock { Text = "No Media", Foreground = Brushes.White, FontSize = 13, FontWeight = FontWeights.Bold, HorizontalAlignment = HorizontalAlignment.Center };
            artistLabel = new TextBlock { Text = "Waiting...", Foreground = Brushes.Gray, FontSize = 11, HorizontalAlignment = HorizontalAlignment.Center };
            
            var btnStack = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center, Margin = new Thickness(0,10,0,10) };
            
            shufBtn = CreateBtn("🔀", 30);
            var prevBtn = CreateBtn("⏮", 30);
            playBtn = CreateBtn("⏯", 45, "#1DB954");
            var nextBtn = CreateBtn("⏭", 30);
            repBtn = CreateBtn("🔁", 30);

            btnStack.Children.Add(shufBtn);
            btnStack.Children.Add(prevBtn);
            btnStack.Children.Add(playBtn);
            btnStack.Children.Add(nextBtn);
            btnStack.Children.Add(repBtn);

            stack.Children.Add(sourceLabel);
            stack.Children.Add(titleLabel);
            stack.Children.Add(artistLabel);
            stack.Children.Add(btnStack);
            
            mainFrame.Child = stack;
            this.Content = mainFrame;

            // Media Commands
            prevBtn.Click += async (s, e) => (await GetSession())?.TrySkipPreviousAsync();
            nextBtn.Click += async (s, e) => (await GetSession())?.TrySkipNextAsync();
            playBtn.Click += async (s, e) => (await GetSession())?.TryTogglePlayPauseAsync();
        }

        private Button CreateBtn(string text, double width, string hex = "Transparent") {
            var b = new Button { 
                Content = text, Width = width, Height = 35, 
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex)),
                Foreground = hex == "#1DB954" ? Brushes.Black : Brushes.White,
                BorderThickness = new Thickness(0), Margin = new Thickness(2)
            };
            return b;
        }

        private void SetupTrigger()
        {
            triggerWindow = new Window {
                Width = 8, Height = 40, WindowStyle = WindowStyle.None, Topmost = true,
                ShowInTaskbar = false, Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1DB954")),
                Left = SystemParameters.PrimaryScreenWidth - 8,
                Top = (SystemParameters.PrimaryScreenHeight / 2) - 20
            };
            triggerWindow.MouseEnter += (s, e) => {
                this.Left = SystemParameters.PrimaryScreenWidth - 250;
                this.Top = (SystemParameters.PrimaryScreenHeight / 2) - 75;
                this.Visibility = Visibility.Visible;
            };
            this.MouseLeave += (s, e) => this.Visibility = Visibility.Collapsed;
            triggerWindow.Show();
        }

        private async void StartMediaPolling()
        {
            updateTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1.5) };
            updateTimer.Tick += async (s, e) => {
                var session = await GetSession();
                if (session != null) {
                    var props = await session.TryGetMediaPropertiesAsync();
                    var timeline = session.GetTimelineProperties();
                    titleLabel.Text = props.Title;
                    artistLabel.Text = props.Artist;
                    sourceLabel.Text = "• " + session.SourceAppUserModelId.Split('!')[0].Split('\\').Last().ToUpper();
                    shufBtn.Foreground = timeline.IsShuffleActive == true ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#1DB954")) : Brushes.White;
                }
            };
            updateTimer.Start();
        }

        private async System.Threading.Tasks.Task<GlobalSystemMediaTransportControlsSession> GetSession() {
            var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
            return manager.GetCurrentSession();
        }
    }
}
