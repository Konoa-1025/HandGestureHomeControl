using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
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

        private void NTimer_Tick(object sender, EventArgs e)
        {
            DateTime NowTime = DateTime.Now;
            NTimeLB.Text = NowTime.ToString("HH:mm:ss");
        }

        private void SendCommand()
        {
            string command = UConsole.Text.Trim();

            if (string.IsNullOrWhiteSpace(command))
                return;

            if (command == "ここにコマンドを入力してください")
                return;

            Console.AppendText("> " + command + Environment.NewLine);

            // ↓ 追加
            Console.SelectionStart = Console.TextLength;
            Console.ScrollToCaret();

            string result = _console.Execute(command);

            if (!string.IsNullOrEmpty(result))
            {
                Console.AppendText(result + Environment.NewLine);

                // ↓ 追加
                Console.SelectionStart = Console.TextLength;
                Console.ScrollToCaret();
            }

            UConsole.Clear();
        }

        private async void Form1_Load(object sender, EventArgs e)
        {
            await Initialize();
        }

        public async Task Initialize() //初期化
        {
            NTimeLB.Text = "";
            Console.Text = "";
            NTimer.Start();

            await SetLamp(P0Sign, LampState.Success);
            await SetLamp(P1Sign, LampState.Error);
            await SetLamp(P2Sign, LampState.Disconnected);
            await SetLamp(P3Sign, LampState.Idle);
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

        private void textBox1_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                SendCommand();

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
            Console.Text = "";
        }

        private void Chelp_Click(object sender, EventArgs e)
        {
            UConsole.Text = "help";
            SendCommand();
        }
    }
}
