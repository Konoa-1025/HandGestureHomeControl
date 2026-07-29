using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;



namespace HandGestureDashboard
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private readonly ConsoleManager _console = new ConsoleManager();

        private readonly List<string> _commandHistory = new List<string>();
        private int _historyIndex = 0;
        private string _currentInput = "";

        private TcpListener tcpListener;
        private TcpClient tcpClient;
        private CancellationTokenSource cancellationTokenSource =
    new CancellationTokenSource();
        public string Command { get; set; }

        private void NTimer_Tick(object sender, EventArgs e)
        {
            DateTime NowTime = DateTime.Now;
            NTimeLB.Text = NowTime.ToString("HH:mm:ss");
        }

        private async Task SendCommand()
        {
            string command = UConsole.Text.Trim();

            if (_shellMode)
            {
                string output = await RunPowerShellAsync(command);
                ConsoleWriteLine(output);

                UConsole.Clear();
                return;
            }

            if (string.IsNullOrWhiteSpace(command))
                return;

            if (command == "ここにコマンドを入力してください")
                return;

            if (_commandHistory.Count == 0 ||
                _commandHistory[_commandHistory.Count - 1] != command)
            {
                _commandHistory.Add(command);
            }

            _historyIndex = _commandHistory.Count;
            _currentInput = "";

            ConsoleWriteLine("> " + command);

            ConsoleCommandResult result = _console.Execute(command);

            switch (result.Type)
            {
                case ConsoleCommandType.Clear:
                    Console.Clear();
                    break;

                case ConsoleCommandType.Exit:
                    Close();
                    break;

                case ConsoleCommandType.Save:
                    SaveSettings();
                    break;

                case ConsoleCommandType.TcpStart:
                    StartTcp();
                    break;

                case ConsoleCommandType.TcpStop:
                    StopTcp();
                    break;

                case ConsoleCommandType.TcpList:
                    ShowTcpList();
                    break;

                case ConsoleCommandType.TcpEdit:
                    EditTcpPort(
                        result.PortIndex,
                        result.PortNumber
                    );
                    break;

                case ConsoleCommandType.PowerShell:
                    try
                    {
                        ConsoleWriteLine(
                            "PowerShellを実行しています: " +
                            result.Command
                        );

                        string output =
                            await RunPowerShellAsync(result.Command);

                        ConsoleWriteLine(output);
                    }
                    catch (Exception ex)
                    {
                        ConsoleWriteLine(
                            "PowerShellの実行中にエラーが発生しました。"
                        );

                        ConsoleWriteLine(ex.Message);
                    }
                    break;

                case ConsoleCommandType.Message:
                    if (!string.IsNullOrEmpty(result.Message))
                    {
                        ConsoleWriteLine(result.Message);
                    }
                    break;
            }

            UConsole.Clear();
        }

        private async Task<string> RunPowerShellAsync(string command)
        {
            using (Process process = new Process())
            {
                process.StartInfo.FileName = "powershell.exe";

                process.StartInfo.Arguments =
                    "-NoProfile -ExecutionPolicy Bypass -Command \"" +
                    command.Replace("\"", "\\\"") +
                    "\"";

                process.StartInfo.RedirectStandardOutput = true;
                process.StartInfo.RedirectStandardError = true;
                process.StartInfo.UseShellExecute = false;
                process.StartInfo.CreateNoWindow = true;

                process.Start();

                Task<string> outputTask =
                    process.StandardOutput.ReadToEndAsync();

                Task<string> errorTask =
                    process.StandardError.ReadToEndAsync();

                await Task.WhenAll(outputTask, errorTask);

                process.WaitForExit();

                string output = outputTask.Result;
                string error = errorTask.Result;

                if (!string.IsNullOrWhiteSpace(error))
                {
                    if (!string.IsNullOrWhiteSpace(output))
                    {
                        return output.TrimEnd() +
                            Environment.NewLine +
                            error.TrimEnd();
                    }

                    return error.TrimEnd();
                }

                if (string.IsNullOrWhiteSpace(output))
                {
                    return "PowerShellコマンドを実行しました。";
                }

                return output.TrimEnd();
            }
        }

        private void SaveSettings()
        {
            try
            {
                Properties.Settings.Default.Save();

                ConsoleWriteLine(
                    "設定値の保存が正常に完了しました。"
                );
            }
            catch (Exception ex)
            {
                ConsoleWriteLine(
                    "設定の保存中にエラーが発生しました。"
                );

                ConsoleWriteLine(ex.Message);
            }
        }


        private async Task StartTcp()
        {
            // 必ず最初に生成する
            cancellationTokenSource = new CancellationTokenSource();

            int[] ports =
            {
        Properties.Settings.Default.port0,
        Properties.Settings.Default.port1,
        Properties.Settings.Default.port2,
        Properties.Settings.Default.port3,
        Properties.Settings.Default.port4,
        Properties.Settings.Default.port5
    };

            List<Task> tasks = new List<Task>();

            foreach (int port in ports)
            {
                tasks.Add(
                    StartTcpServerAsync(
                        port,
                        cancellationTokenSource.Token
                    )
                );
            }

            await Task.WhenAll(tasks);
        }

        private void StopTcp()
        {
            StopReceive();
            ConsoleWriteLine("TCPサーバーを停止しました。");
        }

        private void ShowTcpList()
        {
            string state = "listen";

            ConsoleWriteLine(
                "TCP接続中のクライアント一覧\n" +
                "Port0: " + Properties.Settings.Default.port0 + " " + state + "\n" +
                "Port1: " + Properties.Settings.Default.port1 + " " + state + "\n" +
                "Port2: " + Properties.Settings.Default.port2 + " " + state + "\n" +
                "Port3: " + Properties.Settings.Default.port3 + " " + state + "\n" +
                "Port4: " + Properties.Settings.Default.port4 + " " + state + "\n" +
                "Port5: " + Properties.Settings.Default.port5 + " " + state
            );
        }

        private void EditTcpPort(int portIndex, int portNumber)
        {
            switch (portIndex)
            {
                case 0:
                    Properties.Settings.Default.port0 = portNumber;
                    port0Lb.Text = portNumber.ToString();
                    break;

                case 1:
                    Properties.Settings.Default.port1 = portNumber;
                    port1Lb.Text = portNumber.ToString();
                    break;

                case 2:
                    Properties.Settings.Default.port2 = portNumber;
                    port2Lb.Text = portNumber.ToString();
                    break;

                case 3:
                    Properties.Settings.Default.port3 = portNumber;
                    port3Lb.Text = portNumber.ToString();
                    break;

                case 4:
                    Properties.Settings.Default.port4 = portNumber;
                    break;

                case 5:
                    Properties.Settings.Default.port5 = portNumber;
                    break;

                default:
                    ConsoleWriteLine(
                        "存在しないポート番号です。"
                    );
                    return;
            }

            ConsoleWriteLine(
                "port" + portIndex +
                " を " + portNumber +
                " に変更しました。"
            );
        }

        private async void Form1_Load(object sender, EventArgs e)
        {
            await Initialize();
        }

        public async Task Initialize() //初期化
        {
            this.Size = new Size(796, 475);

            NTimeLB.Text = "";
            Console.Text = "";
            NTimer.Start();

            await SetLamp(P0Sign, LampState.Success);
            await SetLamp(P1Sign, LampState.Error);
            await SetLamp(P2Sign, LampState.Disconnected);
            await SetLamp(P3Sign, LampState.Idle);

            port0Lb.Text = Properties.Settings.Default.port0.ToString();
            port1Lb.Text = Properties.Settings.Default.port1.ToString();
            port2Lb.Text = Properties.Settings.Default.port2.ToString();
            port3Lb.Text = Properties.Settings.Default.port3.ToString();
        }

        public enum LampState
        {
            Disconnected,   // 黄色
            Idle,           // グレー
            Success,        // 緑
            Error           // 赤
        }

        private async Task SetLamp(Label lamp, LampState state)
        {
            switch (state)
            {
                case LampState.Disconnected:
                    lamp.ForeColor = Color.Gold;
                    break;

                case LampState.Idle:
                    lamp.ForeColor = Color.Gray;
                    break;

                case LampState.Success:
                    lamp.ForeColor = Color.LimeGreen;
                    await Task.Delay(120);
                    lamp.ForeColor = Color.Gray;
                    break;

                case LampState.Error:
                    lamp.ForeColor = Color.Red;
                    await Task.Delay(120);
                    lamp.ForeColor = Color.Gray;
                    break;
            }
        }

        private async void button1_Click(object sender, EventArgs e)
        {
            await Initialize();
        }

        //-------------------------
        //  コンソールのシステム
        //-------------------------

        private async void textBox1_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                await SendCommand();

                e.SuppressKeyPress = true;
                return;
            }

            if (e.KeyCode == Keys.Up)
            {
                ShowPreviousCommand();
                e.SuppressKeyPress = true;
                return;
            }

            if (e.KeyCode == Keys.Down)
            {
                ShowNextCommand();
                e.SuppressKeyPress = true;
            }
        }

        private void UConsole_MouseDown(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left &&
                UConsole.Text == "ここにコマンドを入力してください")
            {
                UConsole.Clear();
            }
        }

        private void ConsoleWriteLine(string text)
        {
            if (_shellMode)
            {
                _shellLog += text + Environment.NewLine;
            }
            else
            {
                _consoleLog += text + Environment.NewLine;
            }

            Console.AppendText(text + Environment.NewLine);

            Console.SelectionStart = Console.TextLength;
            Console.ScrollToCaret();
        }

        private void UConsole_MouseLeave(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(UConsole.Text))
            {
                UConsole.Text = "ここにコマンドを入力してください";
            }
        }

        private void CClear_Click(object sender, EventArgs e)
        {
            Console.Text = ">";
        }

        private async void Chelp_Click(object sender, EventArgs e)
        {
            UConsole.Text = "help";
            await SendCommand();
        }

        private void button2_Click(object sender, EventArgs e)
        {
            if (button2.Text == "コンソール")
            {
                button2.Text = "ノーマル";
                this.Size = new Size(796, 664);
            }
            else
            {
                button2.Text = "コンソール";
                this.Size = new Size(796, 475);
            }

        }

        private void ShowPreviousCommand()
        {
            if (_commandHistory.Count == 0)
                return;

            // 履歴を見始める直前の入力内容を保存
            if (_historyIndex == _commandHistory.Count)
            {
                _currentInput = UConsole.Text;
            }

            if (_historyIndex > 0)
            {
                _historyIndex--;
                UConsole.Text = _commandHistory[_historyIndex];

                // カーソルを末尾へ
                UConsole.SelectionStart = UConsole.Text.Length;
            }
        }

        private void ShowNextCommand()
        {
            if (_commandHistory.Count == 0)
                return;

            if (_historyIndex < _commandHistory.Count - 1)
            {
                _historyIndex++;
                UConsole.Text = _commandHistory[_historyIndex];
            }
            else
            {
                // 最新履歴より先へ進んだら、元の入力へ戻す
                _historyIndex = _commandHistory.Count;
                UConsole.Text = _currentInput;
            }

            // カーソルを末尾へ
            UConsole.SelectionStart = UConsole.Text.Length;
        }

        private void UConsole_TextChanged(object sender, EventArgs e)
        {

        }
        private string _consoleLog = "";
        private string _shellLog = "";
        private bool _shellMode = false;
        private void label4_Click(object sender, EventArgs e)
        {
            label10.ForeColor = Color.Gray;
            label4.ForeColor = Color.Yellow;

            _shellMode = true;

            UConsole.ForeColor = Color.Yellow;
            label20.Text = "_>";
            label20.ForeColor = Color.Yellow;
            Console.ForeColor = Color.Yellow;

            _consoleLog = Console.Text;
            Console.Text = _shellLog;
        }

        private void label10_Click(object sender, EventArgs e)
        {
            _shellMode = false;

            label10.ForeColor = Color.Yellow;
            label4.ForeColor = Color.Gray;

            label20.Text = ">";

            UConsole.ForeColor = Color.LimeGreen;
            label20.ForeColor = Color.LimeGreen;
            Console.ForeColor = Color.LimeGreen;

            _shellLog = Console.Text;
            Console.Text = _consoleLog;
        }


        //-------------------------
        //tcp
        //-------------------------

        private async Task StartTcpServerAsync(int port,CancellationToken cancellationToken)
        {
            tcpListener = new TcpListener(IPAddress.Any, port);
            tcpListener.Start();

            AppendLog($"TCPサーバー起動: ポート {port}");
            AppendLog("接続待機中...");

            while (!cancellationToken.IsCancellationRequested)
            {
                tcpClient = await tcpListener.AcceptTcpClientAsync();

                AppendLog(
                    $"接続されました: {tcpClient.Client.RemoteEndPoint}"
                );

                try
                {
                    await ReceiveAsync(tcpClient, cancellationToken);
                }
                catch (Exception ex)
                {
                    AppendLog($"受信エラー: {ex.Message}");
                }
                finally
                {
                    tcpClient.Close();
                    tcpClient = null;

                    AppendLog("クライアントが切断されました。");
                    AppendLog("再接続を待機します...");
                }
            }
        }

        private async Task ReceiveAsync(TcpClient client,CancellationToken cancellationToken)
        {
            NetworkStream stream = client.GetStream();

            StreamReader reader = new StreamReader(
                stream,
                Encoding.UTF8
            );

            while (!cancellationToken.IsCancellationRequested)
            {
                string line = await reader.ReadLineAsync();

                if (line == null)
                {
                    break;
                }

                AppendLog(line);
            }
        }


        private void StopReceive()
        {
            cancellationTokenSource?.Cancel();

            tcpListener?.Stop();
            tcpListener = null;

            AppendLog("TCP停止");
        }

        private const int MaxLogCount = 1000;

        private void AppendLog(string message)
        {
            if (IsDisposed || Disposing || LogBox.IsDisposed)
            {
                return;
            }

            string log = $"[{DateTime.Now:HH:mm:ss}] {message}";

            if (LogBox.InvokeRequired)
            {
                try
                {
                    LogBox.BeginInvoke(new Action(() => AddLogItem(log)));
                }
                catch (InvalidOperationException)
                {
                    // フォーム終了中など
                }

                return;
            }

            AddLogItem(log);
        }

        private void AddLogItem(string log)
        {
            LogBox.Items.Add(log);

            if (LogBox.Items.Count > MaxLogCount)
            {
                LogBox.Items.RemoveAt(0);
            }

            if (LogBox.Items.Count > 0)
            {
                LogBox.TopIndex = LogBox.Items.Count - 1;
            }
        }

    }
}




