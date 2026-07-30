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
    public partial class Hand : Form
    {
        public Hand()
        {
            InitializeComponent();
        }

        private void Hand_Load(object sender, EventArgs e)
        {

        }

        public void SetGesture(string gesture)
        {
            switch (gesture)
            {
                case "FIST":
                    BackgroundImage = Properties.Resources.gu;
                    BackColor = Color.Red;
                    break;

                case "OPEN_HAND":
                    BackgroundImage = Properties.Resources.pa;
                    BackColor = Color.Lime;
                    break;

                case "PEACE":
                    BackgroundImage = Properties.Resources.choki;
                    BackColor = Color.DeepSkyBlue;
                    break;

                case "POINT":
                    BackgroundImage = Properties.Resources.hitosashiyubi;
                    BackColor = Color.Orange;
                    break;

                default:
                    BackgroundImage = Properties.Resources.question;
                    BackColor = Color.Gray;
                    break;
            }
        }

        public void Reset()
        {
            BackgroundImage = Properties.Resources.question;
            BackColor = Color.Gray;
        }

    }
}
