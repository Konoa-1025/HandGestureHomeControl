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
    public partial class MeasurementInfo : Form
    {
        public MeasurementInfo()
        {
            InitializeComponent();
        }

        private void MeasurementInfo_Load(object sender, EventArgs e)
        {
            ResetInfo();
        }

        private void HandNmLb_Click(object sender, EventArgs e)
        {
            // ハンド番号
        }

        private void TimeLb_Click(object sender, EventArgs e)
        {
            // 00.0秒
        }

        private void countLb_Click(object sender, EventArgs e) 
        {
            // 現在 /全件数
        }

        /// <summary>
        /// 表示を更新する
        /// </summary>
        public void UpdateInfo(
    int handNumber,
    double remainingSeconds,
    int current,
    int total)
        {
            remainingSeconds = Math.Max(0, remainingSeconds);

            HandNmLb.Text = $"Hand No.{handNumber}";
            TimeLb.Text = $"{remainingSeconds:0.0}秒";
            countLb.Text = $"{current} / {total}";
        }

        /// <summary>
        /// 初期表示
        /// </summary>
        public void ResetInfo()
        {
            HandNmLb.Text = "Hand No.-";
            TimeLb.Text = "0.0秒";
            countLb.Text = "0 / 0";
        }
    }
}
