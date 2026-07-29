using HandGestureHomeControl;
using K4os.Compression.LZ4.Streams;
using Newtonsoft.Json;
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

        private readonly Dictionary<string, PendingFileTransfer>
    _pendingFileTransfers =
        new Dictionary<string, PendingFileTransfer>();

        private readonly object _fileTransferLock =
            new object();

        //==============================================================
        // 研究データ
        //==============================================================
        private ResearchData _latestResearchData;

        public ResearchData LatestResearchData
        {
            get { return _latestResearchData; }
        }


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
                    port4Lb.Text = portNumber.ToString();
                    port4PLb.Text = portNumber.ToString();
                    break;

                case 5:
                    Properties.Settings.Default.port5 = portNumber;
                    port5Lb.Text = portNumber.ToString();
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

        //==============================================================
        // 初期化
        //==============================================================
        public async Task Initialize()
        {
            UpdateIPAddress();

            // 起動中のときだけ停止する
            if (_tcpRunning)
            {
                StopTcp(false);
            }

            this.Size = new Size(937, 475);

            NTimeLB.Text = "";
            Console.Text = "";
            NTimer.Start();

            await SetAllPortLamps(LampState.Disconnected);

            port0Lb.Text = Properties.Settings.Default.port0.ToString();
            port1Lb.Text = Properties.Settings.Default.port1.ToString();
            port2Lb.Text = Properties.Settings.Default.port2.ToString();
            port3Lb.Text = Properties.Settings.Default.port3.ToString();
            port4Lb.Text = Properties.Settings.Default.port4.ToString();
            port5Lb.Text = Properties.Settings.Default.port5.ToString();

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

            if (port == Properties.Settings.Default.port4)
                return P4Sign;

            if (port == Properties.Settings.Default.port5)
                return P5Sign;

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
            await SetLamp(P1Sign, state);
            await SetLamp(P2Sign, state);
            await SetLamp(P3Sign, state);
            await SetLamp(P4Sign, state);
            await SetLamp(P5Sign, state);

            SetControlText(P0statusLb, state.ToString());
            SetControlText(P1statusLb, state.ToString());
            SetControlText(P2statusLb, state.ToString());
            SetControlText(P3statusLb, state.ToString());
            SetControlText(P4statusLb, state.ToString());
            SetControlText(P5statusLb, state.ToString());
        }

        //==============================================================
        // UIスレッド安全更新
        //==============================================================
        private void SetControlText(Control control, string text)
        {
            if (control == null ||
                control.IsDisposed ||
                IsDisposed ||
                Disposing)
            {
                return;
            }

            if (control.InvokeRequired)
            {
                try
                {
                    control.BeginInvoke(new Action(() =>
                    {
                        control.Text = text;
                    }));
                }
                catch (InvalidOperationException)
                {
                    // フォーム終了中
                }

                return;
            }

            control.Text = text;
        }

        private Label GetPortStatusLabel(int port)
        {
            if (port == Properties.Settings.Default.port0)
                return P0statusLb;

            if (port == Properties.Settings.Default.port1)
                return P1statusLb;

            if (port == Properties.Settings.Default.port2)
                return P2statusLb;

            if (port == Properties.Settings.Default.port3)
                return P3statusLb;

            if (port == Properties.Settings.Default.port4)
                return P4statusLb;

            if (port == Properties.Settings.Default.port5)
                return P5statusLb;

            return null;
        }

        private void SetPortStatus(int port, string status)
        {
            SetControlText(GetPortStatusLabel(port), status);
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


            try
            {
                await Task.WhenAll(serverTasks);
            }
            catch (OperationCanceledException)
            {
                // StopTcpによる正常な停止

            }
            catch (Exception ex)
            {
                AppendLog(
                    "TCPサーバー全体でエラーが発生しました: " +
                    ex.Message
                );

            }
            finally
            {
                _tcpRunning = false;
            }
        }

        //==============================================================
        // IPアドレス取得
        //==============================================================
        private void UpdateIPAddress(bool forceUpdate = false)
        {
            string ip = "取得できません";

            try
            {
                IPAddress selectedAddress =
                    Dns.GetHostEntry(Dns.GetHostName())
                    .AddressList
                    .Where(address =>
                        address.AddressFamily ==
                        AddressFamily.InterNetwork)
                    .OrderBy(address =>
                        address.ToString().StartsWith("169.254.") ? 1 : 0)
                    .FirstOrDefault();

                if (selectedAddress != null)
                {
                    ip = selectedAddress.ToString();
                }
            }
            catch (Exception ex)
            {
                AppendLog(
                    "IPアドレス取得エラー: " + ex.Message
                );
            }

            SetControlText(IPLb, "IP:" + ip);

            if (forceUpdate)
            {
                ConsoleWriteLine(
                    "IPアドレス: " + ip
                );
            }
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
                SetPortStatus(port, "Listening");

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
                    SetPortStatus(port, "Connected");

                    // 受信中でも次のクライアントを受け付ける

                    if (port == Properties.Settings.Default.port5)
                    {
                        _lastLoggedTransferProgress = -1;
                        ResetFileTransferProgress();

                        _ = ReceiveCompressedFileAsync(
                            client,
                            port,
                            cancellationToken
                        );
                    }
                    else
                    {
                        _ = ReceiveClientAsync(
                            client,
                            port,
                            cancellationToken
                        );
                    }
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
                    SetPortStatus(port, "Error");
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
                    SetPortStatus(port, "Error");
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
                SetPortStatus(port, "Disconnected");
            }
        }
        private async Task ReceiveClientAsync(TcpClient client,int port,CancellationToken cancellationToken)
        {
            StreamWriter writer = null;
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
                using (StreamReader reader = new StreamReader(
                    stream,
                    Encoding.UTF8,
                    false,
                    1024,
                    true))
                using (writer = new StreamWriter(
                    stream,
                    new UTF8Encoding(false),
                    1024,
                    true))
                {
                    writer.AutoFlush = true;
                    RegisterTcpWriter(port, writer);

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

                if (writer != null)
                {
                    UnregisterTcpWriter(port, writer);
                }

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
                        SetPortStatus(port, "Listening");
                    }
                    else
                    {
                        await SetPortLamp(
                            port,
                            LampState.Connected
                        );
                        SetPortStatus(port, "Connected");
                    }
                }
            }
        }

        //==============================================================
        // 受信データ振り分け
        //==============================================================
        private void ProcessReceivedData(int port, string data)
        {
            if (port == Properties.Settings.Default.port4)
            {
                if (TryHandlePrepareResponse(data))
                {
                    AppendLog("計測準備結果を認識しました。");
                    return;
                }


                if (TryHandleDataListResponse(data))
                    return;

                if (TryHandleDataInfoResponse(data))
                    return;
            }

            if (string.IsNullOrWhiteSpace(data))
                return;

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

        }

        //==============================================================
        // Port1：研究JSONデータ
        //==============================================================
        private void HandlePort1Data(string json)
        {
            if (TryHandlePrepareResponse(json))
            {
                return;
            }

            ResearchData researchData;

            if (!ResearchManager.TryParse(
                json,
                out researchData))
            {
                AppendPortLog(
                    Properties.Settings.Default.port1,
                    "JSON解析失敗"
                );

                return;
            }

            _latestResearchData = researchData;

            if (InvokeRequired)
            {
                BeginInvoke(new Action(() =>
                {
                    ProcessResearchData(researchData);
                }));

                return;
            }

            ProcessResearchData(researchData);
        }

        //==============================================================
        // 研究データを使った条件分岐
        //==============================================================
        double FPS;
        private void ProcessResearchData(
            ResearchData data)
        {
            AppendPortLog(
    Properties.Settings.Default.port1,
    JsonConvert.SerializeObject(data)
);
            /*
             * ここへ自由にif文を追加する。
             *
             * 例:
             * if (data.Recognition != null &&
             *     data.Recognition.StableGesture == "FIST")
             * {
             *     // グーを認識した時の処理
             * }
             */

            if (data.Recognition != null &&
                data.Recognition.HandDetected)
            {
                // 手を検出した時
            }

            if (data.Recognition == null)
            {
                NowGesPicture.Image = Properties.Resources.question;
            }
            else
            {
                switch (data.Recognition.StableGesture)
                {
                    case "OPEN_HAND":
                        NowGesPicture.Image = Properties.Resources.pa;
                        break;

                    case "FIST":
                        NowGesPicture.Image = Properties.Resources.gu;
                        break;

                    case "PEACE":
                        NowGesPicture.Image = Properties.Resources.choki;
                        break;

                    case "POINT":
                        NowGesPicture.Image = Properties.Resources.hitosashiyubi;
                        break;

                    default:
                        NowGesPicture.Image = Properties.Resources.question;
                        break;
                }
            }


            if (data.Experiment != null &&
                data.Recognition != null &&
                !string.IsNullOrWhiteSpace(
                    data.Experiment.ExpectedGesture) &&
                data.Experiment.ExpectedGesture ==
                data.Recognition.StableGesture)
            {
                // 期待ジェスチャーと認識結果が一致した時
            }

            if (data.System != null)
            {
                CPULb.Text = data.System.CpuPercent.ToString() + "%";
            }
            else
            {
                CPULb.Text = "N/A";
            }

            if (data.System != null && data.System.GpuPercent.HasValue)
            {
                GPULb.Text = data.System.GpuPercent.HasValue + "%";
            }
            else
            {
                GPULb.Text = "N/A";
            }

            if (data.System != null)
            {
                MEMLb.Text = data.System.MemoryPercent.ToString() + "%";
            }
            else
            {
                MEMLb.Text = "N/A";
            }

            if (data.System != null)
            {
                FPS = Math.Floor(data.Performance.Fps);
            }

            if (data.System != null && data.Performance.VideoLatencyMs != null)
            {
                FPSLb.Text = FPS.ToString() +" / ";
            }
            else
            {
                FPSLb.Text = FPS.ToString() + " / " + "N/A";
            }

            if (data.System != null &&
                data.System.GpuPercent.HasValue &&
                data.System.GpuPercent.Value >= 80.0)
            {
                // GPU使用率が取得でき、80%以上
            }

            if (data.Performance != null &&
                data.Performance.Fps < 10.0)
            {
                // FPSが10未満
            }

            

            if (data.Model == null)
            {
                ModelLb.Text = "Model NULL";
            }
            else
            {
                switch (data.Model.Current)
                {
                    case "high":
                        ModelLb.Text = "High Model";
                        break;

                    case "low":
                        ModelLb.Text = "Low Model";
                        break;

                    case "standby":
                        ModelLb.Text = "Standby Model";
                        break;

                    case null:
                    case "":
                        ModelLb.Text = "Current NULL";
                        break;

                    default:
                        ModelLb.Text =
                            data.Model.Current + " ?";
                        break;
                }
            }
        }

        //==============================================================
        // その他ポート専用処理
        //==============================================================
        private void HandlePort0Data(string data)
        {
            // port0専用処理
        }

        private void HandlePort2Data(string data)
        {
            // port2専用処理
        }

        private void HandlePort3Data(string data)
        {
            // port3専用処理
        }

        private void HandlePort4Data(string data)
        {
            // port4専用処理
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

        //==============================================================
        // TCP停止
        //==============================================================
        private void StopTcp(bool showMessage = true)
        {
            if (!_tcpRunning)
            {
                if (showMessage)
                {
                    ConsoleWriteLine(
                        "TCPサーバーは起動していません。"
                    );
                }

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

            if (showMessage)
            {
                ConsoleWriteLine(
                    "TCPサーバーを停止しました。"
                );
            }

            AppendLog(
                "すべてのTCPサーバーを停止しました。"
            );

            _ = SetAllPortLamps(
                LampState.Disconnected
            );
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
            StopTcp(false);

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
        //==============================================================
        //計測アプリケーション
        //==============================================================

        bool experimented = false;
        bool failPush = false;
        int count = 8;
        private Hand handForm;
        private Direction directionForm;
        private Camera cameraForm;
        private void button7_Click(object sender, EventArgs e)
        {
            AppendLog("計測開始");
        }

        private async void StartPushBt_Click(object sender, EventArgs e)
        {
                switch (StartPushBt.Text)
            {
                case "計測準備":
                    await PrepareExperimentAsync();
                    break;

                case "計測開始":
                    count = 8;
                    StartPushBt.Enabled = false;
                    CountDown.Start();
                    break;

                case "計測停止":
                    ResetMeasurementPreparation("計測を停止しました。");
                    break;
            }
        }

        private void DataPushTimer_Tick(object sender, EventArgs e)
        {
            if (label9.Text.Length >= 6)
            {
                label9.Text = "送信中";
            }
            else
            {
                label9.Text += ".";
            }
        }

        private void DataPush_Click(object sender, EventArgs e)
        {
            if(exNamebx.Text == "")
            {
                AppendLog("実験名を入力してください。");
                return;
            }
            AppendLog("環境データ送信します。");
            SaveExperimentHistory(exNamebx.Text.Trim(), int.Parse(label34.Text));
            tableLayoutPanel4.Enabled = false;
            DataPushTimer.Start();
            StartPushBt.Enabled = false;
        }

        private void textBox7_TextChanged(object sender, EventArgs e)
        {
            string experimentId = exNamebx.Text.Trim();
            string exList = Properties.Settings.Default.exlist;

            int trial = 1; // 初めてなら1回目

            foreach (string item in exList.Split(','))
            {
                if (string.IsNullOrWhiteSpace(item))
                    continue;

                string[] data = item.Split(' ');

                if (data.Length != 2)
                    continue;

                if (data[0] == experimentId)
                {
                    label33.Visible = true;
                    if (int.TryParse(data[1], out int count))
                    {
                        trial = count + 1;
                        
                    }

                    break;
                }
            }

            label34.Text = trial.ToString();

        }

        private void SaveExperimentHistory(string experimentId, int trialCount)
        {
            List<string> list = new List<string>();
            bool updated = false;

            foreach (string item in Properties.Settings.Default.exlist.Split(','))
            {
                if (string.IsNullOrWhiteSpace(item))
                    continue;

                string[] data = item.Split(' ');

                if (data.Length != 2)
                    continue;

                if (data[0] == experimentId)
                {
                    // 試行回数を更新
                    list.Add($"{experimentId} {trialCount}");
                    updated = true;
                }
                else
                {
                    list.Add(item);
                }
            }

            // 新しい実験IDなら追加
            if (!updated)
            {
                list.Add($"{experimentId} {trialCount}");
            }

            Properties.Settings.Default.exlist = string.Join(",", list) + ",";
            Properties.Settings.Default.Save();
        }

        private void label34_TextChanged(object sender, EventArgs e)
        {
            
        }

        private void button7_Click_1(object sender, EventArgs e)
        {
            SelectCsvFile();
        }
        
        private void button8_Click(object sender, EventArgs e)
        {

            if (handForm != null && !handForm.IsDisposed)
            {
                return;
            }

            handForm = new Hand();
            handForm.FormClosed += (s, args) => handForm = null;
            handForm.Show();
        }

        private void button9_Click(object sender, EventArgs e)
        {
            if(directionForm != null && !directionForm.IsDisposed)
            {
                return;
            }

            directionForm = new Direction();
            directionForm.FormClosed += (s, args) => directionForm = null;
            directionForm.Show();
        }

        private void button10_Click(object sender, EventArgs e)
        {
            if (cameraForm != null && !cameraForm.IsDisposed)
            {
                return;
            }
            cameraForm = new Camera();
            cameraForm.FormClosed += (s, args) => cameraForm = null;
            cameraForm.Show();
        }

        private void button11_Click(object sender, EventArgs e)
        {
            foreach (Form form in Application.OpenForms.Cast<Form>().ToList())
            {
                if (form != this)
                {
                    form.Close();
                }
            }
        }
        private void StartExperiment()
        {
            StartPushBt.Enabled = true;
            StartPushBt.Text = "計測停止";
            StartPushBt.BackColor = Color.FromArgb(255, 128, 128);

            tableLayoutPanel4.Enabled = false;

            if (tabControl3.TabPages.Count > 13)
            {
                tabControl3.SelectedIndex = 13;
            }

            AppendLog("計測開始");
        }
        private void CountDown_Tick(object sender, EventArgs e)
        {
            if(count-- > 0)
            {
                StartPushBt.Text = "計測開始まで" + count.ToString();

            }
            else { 
                CountDown.Stop();
                StartExperiment();
            }
        }

        private async void DataListUpdateBt_Click(object sender, EventArgs e)
        {
            bool sent = await SendJsonToPortAsync(
                Properties.Settings.Default.port4,
                new
                {
                    type = "data_list_request"
                }
            );

            if (!sent)
            {
                AppendLog(
                    "JSONファイル一覧の取得要求に失敗しました。"
                );

                return;
            }

            AppendLog(
                "JSONファイル一覧を要求しました。"
            );
        }

        private async void listBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (listBox1.SelectedItem == null)
            {
                return;
            }

            string fileName =
                listBox1.SelectedItem.ToString();

            bool sent = await SendJsonToPortAsync(
                Properties.Settings.Default.port4,
                new
                {
                    type = "data_info_request",
                    file_name = fileName
                }
            );

            if (!sent)
            {
                AppendLog(
                    "選択したJSONの情報取得に失敗しました。"
                );
            }
        }

        private async void DataExportBt_Click(object sender, EventArgs e)
        {
            if (listBox1.SelectedItem == null)
            {
                MessageBox.Show(
                    "出力するデータを選択してください。",
                    "データ未選択",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );

                return;
            }

            string fileName =
                listBox1.SelectedItem.ToString();

            using (SaveFileDialog dialog =
                new SaveFileDialog())
            {
                dialog.Title =
                    "JSONLデータの保存先を選択";

                dialog.FileName =
                    fileName;

                dialog.Filter =
                    "JSONLファイル (*.jsonl)|*.jsonl|" +
                    "すべてのファイル (*.*)|*.*";

                dialog.DefaultExt =
                    "jsonl";

                dialog.AddExtension =
                    true;

                if (dialog.ShowDialog() !=
                    DialogResult.OK)
                {
                    return;
                }

                string transferId =
                    Guid.NewGuid().ToString("N");

                PendingFileTransfer transfer =
                    new PendingFileTransfer
                    {
                        TransferId = transferId,
                        FileName = fileName,
                        SavePath = dialog.FileName
                    };

                lock (_fileTransferLock)
                {
                    _pendingFileTransfers[transferId] =
                        transfer;
                }

                DataExportRequest request =
                    new DataExportRequest
                    {
                        Type = "data_export_request",
                        TransferId = transferId,
                        FileName = fileName,
                        TransferPort =
                            Properties.Settings.Default.port5
                    };

                bool sent =
                    await SendJsonToPortAsync(
                        Properties.Settings.Default.port4,
                        request
                    );

                if (!sent)
                {
                    lock (_fileTransferLock)
                    {
                        _pendingFileTransfers.Remove(
                            transferId
                        );
                    }

                    AppendLog(
                        "データ出力要求の送信に失敗しました。"
                    );

                    return;
                }

                DataExportBt.Enabled = false;

                AppendLog(
                    $"データ出力要求送信: {fileName}"
                );
            }
        }

        private async Task ReceiveCompressedFileAsync(
    TcpClient client,
    int port,
    CancellationToken cancellationToken)
        {
            string remoteEndPoint = "不明";
            string temporaryPath = null;
            string finalPath = null;
            string transferId = null;

            bool completed = false;


            try
            {
                if (client.Client.RemoteEndPoint != null)
                {
                    remoteEndPoint =
                        client.Client.RemoteEndPoint.ToString();
                }

                using (client)
                using (NetworkStream networkStream =
                    client.GetStream())
                {
                    /*
                     * Port5の構造
                     *
                     * 1行目：
                     * JSONヘッダー + \n
                     *
                     * 2行目以降：
                     * LZ4 Frame形式のバイナリ
                     */

                    string headerJson =
                        await ReadHeaderLineAsync(
                            networkStream,
                            cancellationToken
                        );

                    if (string.IsNullOrWhiteSpace(headerJson))
                    {
                        throw new InvalidDataException(
                            "ファイル転送ヘッダーが空です。"
                        );
                    }

                    AppendPortLog(
                        port,
                        "転送ヘッダー受信: " + headerJson
                    );

                    FileTransferHeader header;

                    try
                    {
                        header =
                            JsonConvert.DeserializeObject
                            <FileTransferHeader>(headerJson);
                    }
                    catch (JsonException ex)
                    {
                        throw new InvalidDataException(
                            "転送ヘッダーのJSON解析に失敗しました。",
                            ex
                        );
                    }

                    if (header == null)
                    {
                        throw new InvalidDataException(
                            "転送ヘッダーを取得できませんでした。"
                        );
                    }

                    if (header.Type != "file_transfer")
                    {
                        throw new InvalidDataException(
                            "不明な転送形式です: " +
                            header.Type
                        );
                    }

                    if (string.IsNullOrWhiteSpace(
                        header.TransferId))
                    {
                        throw new InvalidDataException(
                            "transfer_idがありません。"
                        );
                    }

                    if (!string.Equals(
                        header.Compression,
                        "lz4",
                        StringComparison.OrdinalIgnoreCase))
                    {
                        throw new InvalidDataException(
                            "対応していない圧縮形式です: " +
                            header.Compression
                        );
                    }

                    if (header.OriginalSize < 0)
                    {
                        throw new InvalidDataException(
                            "original_sizeが不正です。"
                        );
                    }

                    transferId = header.TransferId;

                    PendingFileTransfer pendingTransfer;

                    lock (_fileTransferLock)
                    {
                        _pendingFileTransfers.TryGetValue(
                            transferId,
                            out pendingTransfer
                        );
                    }

                    if (pendingTransfer == null)
                    {
                        throw new InvalidDataException(
                            "対応する転送要求がありません。"
                        );
                    }

                    /*
                     * Pythonから来たファイル名ではなく、
                     * SaveFileDialogで決めた保存先を使用する。
                     *
                     * Python側から任意のパスを書き込まれることを
                     * 防ぐ意味もある。
                     */
                    finalPath = pendingTransfer.SavePath;
                    temporaryPath = finalPath + ".part";

                    string saveDirectory =
                        Path.GetDirectoryName(finalPath);

                    if (!string.IsNullOrWhiteSpace(
                        saveDirectory))
                    {
                        Directory.CreateDirectory(
                            saveDirectory
                        );
                    }

                    if (File.Exists(temporaryPath))
                    {
                        File.Delete(temporaryPath);
                    }

                    AppendLog(
                        $"LZ4転送開始: {pendingTransfer.FileName}"
                    );

                    AppendLog(
                        $"展開後サイズ: " +
                        $"{FormatFileSize(header.OriginalSize)}"
                    );

                    /*
                     * leaveOpen=trueにして、
                     * LZ4Streamを閉じた時にNetworkStreamまで
                     * 自動で閉じられないようにする。
                     */
                    using (Stream lz4Stream =
                        LZ4Stream.Decode(
                            networkStream,
                            leaveOpen: true
                        ))
                    using (FileStream outputStream =
                        new FileStream(
                            temporaryPath,
                            FileMode.Create,
                            FileAccess.Write,
                            FileShare.None,
                            1024 * 1024,
                            true
                        ))
                    {
                        byte[] buffer =
                            new byte[1024 * 1024];

                        long totalWritten = 0;
                        int lastProgress = -1;

                        Stopwatch stopwatch =
                            Stopwatch.StartNew();

                        while (true)
                        {
                            cancellationToken
                                .ThrowIfCancellationRequested();

                            int read =
                                await lz4Stream.ReadAsync(
                                    buffer,
                                    0,
                                    buffer.Length,
                                    cancellationToken
                                );

                            if (read == 0)
                            {
                                break;
                            }

                            await outputStream.WriteAsync(
                                buffer,
                                0,
                                read,
                                cancellationToken
                            );

                            totalWritten += read;

                            if (header.OriginalSize > 0)
                            {
                                int progress =
                                    (int)Math.Min(
                                        100,
                                        totalWritten * 100L /
                                        header.OriginalSize
                                    );

                                /*
                                 * 1%変化した時だけ更新する。
                                 * 毎チャンクUI更新すると重くなるため。
                                 */
                                if (progress != lastProgress)
                                {
                                    lastProgress = progress;


                                    UpdateFileTransferProgress(
                                        progress,
                                        totalWritten,
                                        header.OriginalSize,
                                        stopwatch.Elapsed
                                    );
                                }
                            }
                        }

                        await outputStream.FlushAsync(
                            cancellationToken
                        );

                        /*
                         * 展開後サイズがヘッダーと一致するか確認。
                         */
                        if (header.OriginalSize > 0 &&
                            totalWritten != header.OriginalSize)
                        {
                            throw new InvalidDataException(
                                "展開後のファイルサイズが一致しません。" +
                                $" 予定={header.OriginalSize}," +
                                $" 実際={totalWritten}"
                            );
                        }
                        UpdateFileTransferProgress(100,totalWritten,header.OriginalSize,stopwatch.Elapsed);

                        stopwatch.Stop();
                    }

                    /*
                     * 既存ファイルがあれば、
                     * ユーザーがSaveFileDialogで上書きを許可済みなので削除。
                     */
                    if (File.Exists(finalPath))
                    {
                        File.Delete(finalPath);
                    }

                    File.Move(
                        temporaryPath,
                        finalPath
                    );

                    completed = true;

                    lock (_fileTransferLock)
                    {
                        _pendingFileTransfers.Remove(
                            transferId
                        );
                    }
                    
                    AppendLog(
                        $"データ出力完了: {finalPath}"
                    );

                    AppendPortLog(
                        port,
                        $"転送完了: {Path.GetFileName(finalPath)}"
                    );

                    SetFileTransferCompleted(
                        finalPath
                    );
                }
            }
            catch (OperationCanceledException)
            {
                AppendLog(
                    "ファイル転送が中止されました。"
                );
            }
            catch (Exception ex)
            {
                AppendLog(
                    "ファイル転送失敗: " +
                    ex.GetType().Name +
                    " / " +
                    ex.Message
                );

                AppendPortLog(
                    port,
                    "転送失敗: " + ex.Message
                );

                await SetPortLamp(
                    port,
                    LampState.Error
                );
            }
            finally
            {
                /*
                 * 失敗時は途中ファイルを消す。
                 */
                if (!completed &&
                    !string.IsNullOrWhiteSpace(
                        temporaryPath))
                {
                    try
                    {
                        if (File.Exists(temporaryPath))
                        {
                            File.Delete(temporaryPath);
                        }
                    }
                    catch (Exception ex)
                    {
                        AppendLog(
                            ".partファイル削除失敗: " +
                            ex.Message
                        );
                    }
                }

                if (!completed &&
                    !string.IsNullOrWhiteSpace(
                        transferId))
                {
                    lock (_fileTransferLock)
                    {
                        _pendingFileTransfers.Remove(
                            transferId
                        );
                    }
                }

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
                    $"Port {port}: ファイル転送接続終了 " +
                    remoteEndPoint
                );

                if (!cancellationToken
                    .IsCancellationRequested)
                {
                    if (remainingClients == 0)
                    {
                        await SetPortLamp(
                            port,
                            LampState.Idle
                        );

                        SetPortStatus(
                            port,
                            "Listening"
                        );
                    }
                    else
                    {
                        await SetPortLamp(
                            port,
                            LampState.Connected
                        );

                        SetPortStatus(
                            port,
                            "Connected"
                        );
                    }
                }

                SetDataExportButtonEnabled(true);
            }
        }

        private async Task<string> ReadHeaderLineAsync(
    NetworkStream stream,
    CancellationToken cancellationToken)
        {
            const int maxHeaderSize =
                64 * 1024;

            using (MemoryStream headerBuffer =
                new MemoryStream())
            {
                byte[] oneByte = new byte[1];

                while (true)
                {
                    cancellationToken
                        .ThrowIfCancellationRequested();

                    int read =
                        await stream.ReadAsync(
                            oneByte,
                            0,
                            1,
                            cancellationToken
                        );

                    if (read == 0)
                    {
                        throw new EndOfStreamException(
                            "ヘッダー受信中に接続が切断されました。"
                        );
                    }

                    /*
                     * 改行でJSONヘッダー終了
                     */
                    if (oneByte[0] == (byte)'\n')
                    {
                        break;
                    }

                    /*
                     * Windows形式の\r\nにも対応。
                     * \rは保存しない。
                     */
                    if (oneByte[0] != (byte)'\r')
                    {
                        headerBuffer.WriteByte(
                            oneByte[0]
                        );
                    }

                    if (headerBuffer.Length >
                        maxHeaderSize)
                    {
                        throw new InvalidDataException(
                            "転送ヘッダーが大きすぎます。"
                        );
                    }
                }

                return Encoding.UTF8.GetString(
                    headerBuffer.ToArray()
                );
            }
        }

        private string FormatFileSize(long size)
        {
            double value = size;

            string[] units =
            {
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    };

            int unitIndex = 0;

            while (value >= 1024.0 &&
                   unitIndex <
                   units.Length - 1)
            {
                value /= 1024.0;
                unitIndex++;
            }

            return value.ToString("0.00") +
                " " +
                units[unitIndex];
        }


        private int _lastLoggedTransferProgress = -10;

        private void UpdateFileTransferProgress(
            int progress,
            long writtenBytes,
            long originalSize,
            TimeSpan elapsed)
        {
            progress = Math.Max(0, Math.Min(100, progress));

            // プログレスバーは1％単位で更新
            if (!IsDisposed &&
                !Disposing &&
                progressBar1 != null &&
                !progressBar1.IsDisposed)
            {
                Action updateProgressBar = () =>
                {
                    progressBar1.Value = progress;
                };

                if (progressBar1.InvokeRequired)
                {
                    try
                    {
                        progressBar1.BeginInvoke(updateProgressBar);
                    }
                    catch (InvalidOperationException)
                    {
                        // フォーム終了中
                    }
                }
                else
                {
                    updateProgressBar();
                }
            }

            // 10％以上進んだときだけログへ表示
            if (progress < 100 &&
                progress < _lastLoggedTransferProgress + 10)
            {
                return;
            }

            int loggedProgress =
                progress == 100
                    ? 100
                    : progress / 10 * 10;

            if (loggedProgress ==
                _lastLoggedTransferProgress)
            {
                return;
            }

            _lastLoggedTransferProgress =
                loggedProgress;

            double seconds =
                Math.Max(
                    elapsed.TotalSeconds,
                    0.001
                );

            long speed =
                (long)(writtenBytes / seconds);

            AppendLog(
                $"データ受信中: {loggedProgress}% " +
                $"({FormatFileSize(writtenBytes)} / " +
                $"{FormatFileSize(originalSize)}) " +
                $"{FormatFileSize(speed)}/s"
            );
        }




        private void SetFileTransferCompleted(
    string savedPath)
        {
            if (IsDisposed || Disposing)
            {
                return;
            }

            Action action = () =>
            {
                DataExportBt.Enabled = true;

                MessageBox.Show(
                    "JSONLデータの出力が完了しました。\n\n" +
                    savedPath,
                    "データ出力完了",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            };

            if (InvokeRequired)
            {
                try
                {
                    BeginInvoke(action);
                }
                catch (InvalidOperationException)
                {
                }

                return;
            }

            action();
        }

        private void SetDataExportButtonEnabled(
    bool enabled)
        {
            if (DataExportBt == null ||
                DataExportBt.IsDisposed ||
                IsDisposed ||
                Disposing)
            {
                return;
            }

            if (DataExportBt.InvokeRequired)
            {
                try
                {
                    DataExportBt.BeginInvoke(
                        new Action(() =>
                        {
                            DataExportBt.Enabled =
                                enabled;
                        })
                    );
                }
                catch (InvalidOperationException)
                {
                }

                return;
            }

            DataExportBt.Enabled = enabled;
        }
        private void ResetFileTransferProgress()
        {
            if (progressBar1.InvokeRequired)
            {
                progressBar1.BeginInvoke(new Action(() =>
                {
                    progressBar1.Minimum = 0;
                    progressBar1.Maximum = 100;
                    progressBar1.Value = 0;
                }));

                return;
            }

            progressBar1.Minimum = 0;
            progressBar1.Maximum = 100;
            progressBar1.Value = 0;
        }

    }
}