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
    public partial class Direction : Form
    {
        public Direction()
        {
            InitializeComponent();
        }

        public void SetDirection(string direction)
        {
            switch (direction.ToUpper())
            {
                case "UP":
                    BackgroundImage = Properties.Resources.up;
                    break;

                case "DOWN":
                    BackgroundImage = Properties.Resources.down;
                    break;

                case "LEFT":
                    BackgroundImage = Properties.Resources.left;
                    break;

                case "RIGHT":
                    BackgroundImage = Properties.Resources.right;
                    break;

                default:
                    BackgroundImage = Properties.Resources.noimage;
                    break;
            }
        }
    }
}
