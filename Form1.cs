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

        private CancellationTokenSource _tcpCancellationTokenSource;
        private Task _tcpServerTask;
        private readonly Dictionary<int, TcpListener> _tcpListeners =
            new Dictionary<int, TcpListener>();
        private readonly Dictionary<int, int> _tcpClientCounts =
            new Dictionary<int, int>();
        private readonly object _tcpLock = new object();
        private bool _tcpRunning = false;
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

                case ConsoleCommandType.IP:
                    UpdateIPAddress(true);
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

        private void EditTcpPort(int portIndex, int portNumber)
        {
            switch (portIndex)
            {
                case 0:
                    Properties.Settings.Default.port0 = portNumber;
                    port0Lb.Text = portNumber.ToString();
                    port0PLb.Text = portNumber.ToString();
                    break;

                case 1:
                    Properties.Settings.Default.port1 = portNumber;
                    port1Lb.Text = portNumber.ToString();
                    port1PLb.Text = portNumber.ToString();
                    break;

                case 2:
                    Properties.Settings.Default.port2 = portNumber;
                    port2Lb.Text = portNumber.ToString();
                    port2PLb.Text = portNumber.ToString();
                    break;

                case 3:
                    Properties.Settings.Default.port3 = portNumber;
                    port3Lb.Text = portNumber.ToString();
                    port3PLb.Text = portNumber.ToString();
                    break;

                case 4:
                    Properties.Settings.Default.port4 = portNumber;
                    //port4Lb.Text = portNumber.ToString();
                    port4PLb.Text = portNumber.ToString();
                    break;

                case 5:
                    Properties.Settings.Default.port5 = portNumber;
                    //port5Lb.Text = portNumber.ToString();
                    port5PLb.Text = portNumber.ToString();
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
            UpdateIPAddress();
            StopTcp();

            this.Size = new Size(937, 475);

            NTimeLB.Text = "";
            Console.Text = "";
            NTimer.Start();

            await SetLamp(P0Sign, LampState.Disconnected);
            await SetLamp(P1Sign, LampState.Disconnected);
            await SetLamp(P2Sign, LampState.Disconnected);
            await SetLamp(P3Sign, LampState.Disconnected);

            port0Lb.Text = Properties.Settings.Default.port0.ToString();
            port1Lb.Text = Properties.Settings.Default.port1.ToString();
            port2Lb.Text = Properties.Settings.Default.port2.ToString();
            port3Lb.Text = Properties.Settings.Default.port3.ToString();
            //port4Lb.Text = Properties.Settings.Default.port4.ToString();
            //port5Lb.Text = Properties.Settings.Default.port5.ToString();

            port0PLb.Text = Properties.Settings.Default.port0.ToString();
            port1PLb.Text = Properties.Settings.Default.port1.ToString();
            port2PLb.Text = Properties.Settings.Default.port2.ToString();
            port3PLb.Text = Properties.Settings.Default.port3.ToString();
            port4PLb.Text = Properties.Settings.Default.port4.ToString();
            port5PLb.Text = Properties.Settings.Default.port5.ToString();

            StartTcp();
        }

        public enum LampState
        {
            Disconnected, // 黄色：サーバー停止
            Idle,         // グレー：接続待ち
            Connected,    // 緑：接続中
            Error         // 赤：エラー
        }

        private Task SetLamp(Label lamp, LampState state)
        {
            if (lamp == null ||
                lamp.IsDisposed ||
                IsDisposed ||
                Disposing)
            {
                return Task.CompletedTask;
            }

            if (lamp.InvokeRequired)
            {
                TaskCompletionSource<bool> completionSource =
                    new TaskCompletionSource<bool>();

                try
                {
                    lamp.BeginInvoke(new Action(() =>
                    {
                        try
                        {
                            SetLampColor(lamp, state);
                            completionSource.TrySetResult(true);
                        }
                        catch (Exception ex)
                        {
                            completionSource.TrySetException(ex);
                        }
                    }));
                }
                catch (InvalidOperationException)
                {
                    completionSource.TrySetResult(false);
                }

                return completionSource.Task;
            }

            SetLampColor(lamp, state);
            return Task.CompletedTask;
        }

        private void SetLampColor(Label lamp, LampState state)
        {
            switch (state)
            {
                case LampState.Disconnected:
                    lamp.ForeColor = Color.Gold;
                    break;

                case LampState.Idle:
                    lamp.ForeColor = Color.Gray;
                    break;

                case LampState.Connected:
                    lamp.ForeColor = Color.LimeGreen;
                    break;

                case LampState.Error:
                    lamp.ForeColor = Color.Red;
                    break;
            }
        }

        private Label GetPortLamp(int port)
        {
            if (port == Properties.Settings.Default.port0)
                return P0Sign;

            if (port == Properties.Settings.Default.port1)
                return P1Sign;

            if (port == Properties.Settings.Default.port2)
                return P2Sign;

            if (port == Properties.Settings.Default.port3)
                return P3Sign;

            // P4Sign / P5Sign をフォームに追加した場合はここへ追加する
            return null;
        }

        private Task SetPortLamp(int port, LampState state)
        {
            Label lamp = GetPortLamp(port);

            if (lamp == null)
                return Task.CompletedTask;

            return SetLamp(lamp, state);
        }

        private async Task FlashPortLamp(int port)
        {
            Label lamp = GetPortLamp(port);

            if (lamp == null ||
                lamp.IsDisposed ||
                IsDisposed ||
                Disposing)
            {
                return;
            }

            if (lamp.InvokeRequired)
            {
                TaskCompletionSource<bool> completionSource =
                    new TaskCompletionSource<bool>();

                try
                {
                    lamp.BeginInvoke(new Action(async () =>
                    {
                        try
                        {
                            lamp.ForeColor = Color.White;
                            await Task.Delay(100);
                            lamp.ForeColor = Color.LimeGreen;
                            completionSource.TrySetResult(true);
                        }
                        catch (Exception ex)
                        {
                            completionSource.TrySetException(ex);
                        }
                    }));

                    await completionSource.Task;
                }
                catch (InvalidOperationException)
                {
                    // フォーム終了中
                }

                return;
            }

            lamp.ForeColor = Color.White;
            await Task.Delay(100);
            lamp.ForeColor = Color.LimeGreen;
        }

        private async Task SetAllPortLamps(LampState state)
        {
            await SetLamp(P0Sign, state);
                P0statusLb.Text = state.ToString();
            await SetLamp(P1Sign, state);
                P1statusLb.Text = state.ToString();
            await SetLamp(P2Sign, state);
                P2statusLb.Text = state.ToString();
            await SetLamp(P3Sign, state);
            P3statusLb.Text = state.ToString();
            P4statusLb.Text = state.ToString();
            P5statusLb.Text = state.ToString();
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
                this.Size = new Size(937, 664);
            }
            else
            {
                button2.Text = "コンソール";
                this.Size = new Size(937, 475);
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

        private void StartTcp()
        {
            if (_tcpRunning)
            {
                ConsoleWriteLine("TCPサーバーはすでに起動しています。");
                return;
            }

            int[] ports =
            {
        Properties.Settings.Default.port0,
        Properties.Settings.Default.port1,
        Properties.Settings.Default.port2,
        Properties.Settings.Default.port3,
        Properties.Settings.Default.port4,
        Properties.Settings.Default.port5
    };

            // 同じポート番号が設定されていないか確認
            int[] duplicatePorts = ports
                .GroupBy(port => port)
                .Where(group => group.Count() > 1)
                .Select(group => group.Key)
                .ToArray();

            if (duplicatePorts.Length > 0)
            {
                ConsoleWriteLine(
                    "同じポート番号が複数設定されています: " +
                    string.Join(", ", duplicatePorts)
                );

                return;
            }

            _tcpCancellationTokenSource = new CancellationTokenSource();
            _tcpRunning = true;

            // StartTcpServersAsyncはサーバー停止まで完了しないため、
            // awaitせずTaskとして保持する
            _tcpServerTask = StartTcpServersAsync(
                ports,
                _tcpCancellationTokenSource.Token
            );

            ConsoleWriteLine("TCPサーバーの起動を開始しました。");
        }

        private async Task StartTcpServersAsync(int[] ports, CancellationToken cancellationToken)
        {
            List<Task> serverTasks = new List<Task>();

            foreach (int port in ports)
            {
                serverTasks.Add(
                    StartTcpServerAsync(port, cancellationToken)
                );

            }

            P0statusLb.Text = "Listening";
            P1statusLb.Text = "Listening";
            P2statusLb.Text = "Listening";
            P3statusLb.Text = "Listening";
            P4statusLb.Text = "Listening";
            P5statusLb.Text = "Listening";

            try
            {
                await Task.WhenAll(serverTasks);
            }
            catch (OperationCanceledException)
            {
                // StopTcpによる正常な停止

                P0statusLb.Text = "Disconnected";
                P1statusLb.Text = "Disconnected";
                P2statusLb.Text = "Disconnected";
                P3statusLb.Text = "Disconnected";
                P4statusLb.Text = "Disconnected";
                P5statusLb.Text = "Disconnected";
            }
            catch (Exception ex)
            {
                AppendLog(
                    "TCPサーバー全体でエラーが発生しました: " +
                    ex.Message
                );

                P0statusLb.Text = "Error";
                P1statusLb.Text = "Error";
                P2statusLb.Text = "Error";
                P3statusLb.Text = "Error";
                P4statusLb.Text = "Error";
                P5statusLb.Text = "Error";
            }
            finally
            {
                _tcpRunning = false;
            }
        }

        private void UpdateIPAddress(bool forceUpdate = false)
        {
            string ip = "取得できません";

            foreach (IPAddress address in Dns.GetHostEntry(Dns.GetHostName()).AddressList)
            {
                if (address.AddressFamily == AddressFamily.InterNetwork)
                {
                    ip = address.ToString();
                    break;
                }
            }

            if(forceUpdate == true)
            {
                ConsoleWriteLine("IPアドレス: " + ip);
            }

            IPLb.Text = "IP:"+ip;
        }

        private async Task StartTcpServerAsync(
    int port,
    CancellationToken cancellationToken)
        {
            TcpListener listener = null;

            try
            {
                listener = new TcpListener(IPAddress.Any, port);
                listener.Start();

                lock (_tcpLock)
                {
                    _tcpListeners[port] = listener;
                    _tcpClientCounts[port] = 0;
                }

                AppendLog($"TCPサーバー起動: ポート {port}");
                AppendLog($"Port {port}: 接続待機中");

                await SetPortLamp(port, LampState.Idle);

                while (!cancellationToken.IsCancellationRequested)
                {
                    TcpClient client;

                    try
                    {
                        client = await listener.AcceptTcpClientAsync();
                    }
                    catch (ObjectDisposedException)
                    {
                        // StopTcpでlistener.Stop()された
                        break;
                    }
                    catch (SocketException)
                    {
                        // StopTcpでlistener.Stop()された場合もここへ来る
                        if (cancellationToken.IsCancellationRequested)
                        {
                            break;
                        }

                        throw;
                    }

                    lock (_tcpLock)
                    {
                        _tcpClientCounts[port]++;
                    }

                    AppendLog(
                        $"Port {port}: 接続されました " +
                        $"{client.Client.RemoteEndPoint}"
                    );

                    AppendPortLog(
                        port,
                        $"クライアント接続: {client.Client.RemoteEndPoint}"
                    );

                    await SetPortLamp(port, LampState.Connected);

                    // 受信中でも次のクライアントを受け付ける
                    _ = ReceiveClientAsync(
                        client,
                        port,
                        cancellationToken
                    );
                }
            }
            catch (SocketException ex)
            {
                if (!cancellationToken.IsCancellationRequested)
                {
                    AppendLog(
                        $"Port {port}: Socketエラー: {ex.Message}"
                    );

                    await SetPortLamp(port, LampState.Error);
                }
            }
            catch (Exception ex)
            {
                if (!cancellationToken.IsCancellationRequested)
                {
                    AppendLog(
                        $"Port {port}: サーバーエラー: {ex.Message}"
                    );

                    await SetPortLamp(port, LampState.Error);
                }
            }
            finally
            {
                if (listener != null)
                {
                    try
                    {
                        listener.Stop();
                    }
                    catch
                    {
                        // 停止済みなら何もしない
                    }
                }

                lock (_tcpLock)
                {
                    _tcpListeners.Remove(port);
                    _tcpClientCounts.Remove(port);
                }

                AppendLog($"Port {port}: サーバー停止");

                await SetPortLamp(port, LampState.Disconnected);
            }
        }
        private async Task ReceiveClientAsync(
            TcpClient client,
            int port,
            CancellationToken cancellationToken)
        {
            string remoteEndPoint = "不明";

            try
            {
                if (client.Client.RemoteEndPoint != null)
                {
                    remoteEndPoint =
                        client.Client.RemoteEndPoint.ToString();
                }

                using (client)
                using (NetworkStream stream = client.GetStream())
                using (StreamReader reader =
                    new StreamReader(stream, Encoding.UTF8))
                {
                    while (!cancellationToken.IsCancellationRequested)
                    {
                        string line;

                        try
                        {
                            line = await reader.ReadLineAsync();
                        }
                        catch (IOException)
                        {
                            break;
                        }
                        catch (ObjectDisposedException)
                        {
                            break;
                        }

                        if (line == null)
                        {
                            break;
                        }

                        AppendPortLog(port, line);
                        await FlashPortLamp(port);
                        ProcessReceivedData(port, line);
                    }
                }
            }
            catch (Exception ex)
            {
                if (!cancellationToken.IsCancellationRequested)
                {
                    AppendLog(
                        $"Port {port}: 受信エラー: {ex.Message}"
                    );

                    AppendPortLog(
                        port,
                        $"受信エラー: {ex.Message}"
                    );

                    await SetPortLamp(
                        port,
                        LampState.Error
                    );
                }
            }
            finally
            {
                int remainingClients;

                lock (_tcpLock)
                {
                    if (_tcpClientCounts.ContainsKey(port))
                    {
                        _tcpClientCounts[port]--;

                        if (_tcpClientCounts[port] < 0)
                        {
                            _tcpClientCounts[port] = 0;
                        }

                        remainingClients =
                            _tcpClientCounts[port];
                    }
                    else
                    {
                        remainingClients = 0;
                    }
                }

                AppendLog(
                    $"Port {port}: クライアント切断 {remoteEndPoint}"
                );

                AppendPortLog(
                    port,
                    $"クライアント切断: {remoteEndPoint}"
                );

                if (!cancellationToken.IsCancellationRequested)
                {
                    if (remainingClients == 0)
                    {
                        await SetPortLamp(
                            port,
                            LampState.Idle
                        );
                    }
                    else
                    {
                        await SetPortLamp(
                            port,
                            LampState.Connected
                        );
                    }
                }
            }
        }

        private void ProcessReceivedData(int port, string data)
        {
            if (string.IsNullOrWhiteSpace(data))
                return;

            string normalizedData =
                data.Trim().ToLowerInvariant();

            if (normalizedData.Contains("error"))
            {

                _ = SetPortLamp(
                    port,
                    LampState.Error
                );
            }

            if (normalizedData.Contains("gesture"))
            {
               

                HandleGestureData(port, data);
            }

            if (normalizedData.Contains("cpu"))
            {
                

                HandleCpuData(port, data);
            }

            if (normalizedData.Contains("connected"))
            {
            }

            if (port == Properties.Settings.Default.port0)
            {
                HandlePort0Data(data);
                return;
            }

            if (port == Properties.Settings.Default.port1)
            {
                HandlePort1Data(data);
                return;
            }

            if (port == Properties.Settings.Default.port2)
            {
                HandlePort2Data(data);
                return;
            }

            if (port == Properties.Settings.Default.port3)
            {
                HandlePort3Data(data);
                return;
            }

            if (port == Properties.Settings.Default.port4)
            {
                HandlePort4Data(data);
                return;
            }

            if (port == Properties.Settings.Default.port5)
            {
                HandlePort5Data(data);
            }
        }

        private void HandleGestureData(int port, string data)
        {
            AppendLog(
                $"Port {port}: ジェスチャーデータ処理を実行"
            );
        }

        private void HandleCpuData(int port, string data)
        {
            AppendLog(
                $"Port {port}: CPUデータ処理を実行"
            );
        }

        private void HandlePort0Data(string data)
        {
            // port0専用の処理
        }

        private void HandlePort1Data(string data)
        {
            // port1専用の処理
        }

        private void HandlePort2Data(string data)
        {
            // port2専用の処理
        }

        private void HandlePort3Data(string data)
        {
            // port3専用の処理
        }

        private void HandlePort4Data(string data)
        {
            // port4専用の処理
        }

        private void HandlePort5Data(string data)
        {
            // port5専用の処理
        }

        private ListBox GetPortLogBox(int port)
        {
            if (port == Properties.Settings.Default.port0)
                return Port0LogBox;

            if (port == Properties.Settings.Default.port1)
                return Port1LogBox;

            if (port == Properties.Settings.Default.port2)
                return Port2LogBox;

            if (port == Properties.Settings.Default.port3)
                return Port3LogBox;

            if (port == Properties.Settings.Default.port4)
                return Port4LogBox;

            if (port == Properties.Settings.Default.port5)
                return Port5LogBox;

            return null;
        }

        private void AppendPortLog(int port, string message)
        {
            ListBox targetLogBox = GetPortLogBox(port);

            if (targetLogBox == null ||
                targetLogBox.IsDisposed ||
                IsDisposed ||
                Disposing)
            {
                return;
            }

            string log =
                $"[{DateTime.Now:HH:mm:ss}] {message}";

            if (targetLogBox.InvokeRequired)
            {
                try
                {
                    targetLogBox.BeginInvoke(new Action(() =>
                    {
                        AddPortLogItem(targetLogBox, log);
                    }));
                }
                catch (InvalidOperationException)
                {
                    // フォーム終了中
                }

                return;
            }

            AddPortLogItem(targetLogBox, log);
        }

        private void AddPortLogItem(ListBox targetLogBox, string log)
        {
            targetLogBox.Items.Add(log);

            while (targetLogBox.Items.Count > MaxLogCount)
            {
                targetLogBox.Items.RemoveAt(0);
            }

            if (targetLogBox.Items.Count > 0)
            {
                targetLogBox.TopIndex =
                    targetLogBox.Items.Count - 1;
            }
        }

        private void StopTcp()
        {
            if (!_tcpRunning)
            {
                ConsoleWriteLine(
                    "TCPサーバーは起動していません。"
                );

                return;
            }

            _tcpRunning = false;

            if (_tcpCancellationTokenSource != null)
            {
                _tcpCancellationTokenSource.Cancel();
            }

            List<TcpListener> listeners;

            lock (_tcpLock)
            {
                listeners = _tcpListeners.Values.ToList();
            }

            foreach (TcpListener listener in listeners)
            {
                try
                {
                    listener.Stop();
                }
                catch
                {
                    // すでに停止している場合
                }
            }

            lock (_tcpLock)
            {
                _tcpListeners.Clear();
                _tcpClientCounts.Clear();
            }

            ConsoleWriteLine("TCPサーバーを停止しました。");
            AppendLog("すべてのTCPサーバーを停止しました。");

            _ = SetAllPortLamps(LampState.Disconnected);
        }

        private const int MaxLogCount = 1000;

        private void AppendLog(string message)
        {
            if (IsDisposed ||
                Disposing ||
                LogBox == null ||
                LogBox.IsDisposed)
            {
                return;
            }

            string log =
                $"[{DateTime.Now:HH:mm:ss}] {message}";

            if (LogBox.InvokeRequired)
            {
                try
                {
                    LogBox.BeginInvoke(new Action(() =>
                    {
                        AddLogItem(log);
                    }));
                }
                catch (InvalidOperationException)
                {
                    // フォーム終了中
                }

                return;
            }

            AddLogItem(log);
        }

        private void AddLogItem(string log)
        {
            LogBox.Items.Add(log);

            while (LogBox.Items.Count > MaxLogCount)
            {
                LogBox.Items.RemoveAt(0);
            }

            if (LogBox.Items.Count > 0)
            {
                LogBox.TopIndex =
                    LogBox.Items.Count - 1;
            }
        }

        private void ShowTcpList()
        {
            int[] ports =
            {
        Properties.Settings.Default.port0,
        Properties.Settings.Default.port1,
        Properties.Settings.Default.port2,
        Properties.Settings.Default.port3,
        Properties.Settings.Default.port4,
        Properties.Settings.Default.port5
    };

            StringBuilder text = new StringBuilder();

            text.AppendLine("TCPポート一覧");

            for (int index = 0; index < ports.Length; index++)
            {
                int port = ports[index];

                bool listening;
                int clientCount;

                lock (_tcpLock)
                {
                    listening = _tcpListeners.ContainsKey(port);

                    if (!_tcpClientCounts.TryGetValue(
                        port,
                        out clientCount))
                    {
                        clientCount = 0;
                    }
                }

                string state;

                if (!listening)
                {
                    state = "停止中";
                }
                else if (clientCount == 0)
                {
                    state = "接続待機中";
                }
                else
                {
                    state =
                        "接続中 クライアント数=" +
                        clientCount;
                }

                text.Append(
                    $"Port{index}: {port} {state}"
                );

                if (index < ports.Length - 1)
                {
                    text.AppendLine();
                }
            }

            ConsoleWriteLine(text.ToString());
        }
        protected override void OnFormClosing(
    FormClosingEventArgs e)
        {
            StopTcp();

            if (_tcpCancellationTokenSource != null)
            {
                _tcpCancellationTokenSource.Dispose();
                _tcpCancellationTokenSource = null;
            }

            base.OnFormClosing(e);
        }

        private void button5_Click(object sender, EventArgs e)
        {
            StartTcp();
        }

        private void button4_Click(object sender, EventArgs e)
        {
            StopTcp();
        }
    }
}