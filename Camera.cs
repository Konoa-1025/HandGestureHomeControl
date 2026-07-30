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
    public partial class Camera : Form
    {
        public Camera()
        {
            InitializeComponent();
        }

        private void Camera_Load(object sender, EventArgs e)
        {

        }

        public void SetImage(Image image)
        {
            if (image == null)
                return;

            Image old = this.BackgroundImage;

            BackgroundImage = (Image)image.Clone();

            old?.Dispose();
        }
    }
}
