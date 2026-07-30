namespace HandGestureDashboard
{
    partial class MeasurementInfo
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.HandNmLb = new System.Windows.Forms.Label();
            this.countLb = new System.Windows.Forms.Label();
            this.TimeLb = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // HandNmLb
            // 
            this.HandNmLb.AutoSize = true;
            this.HandNmLb.Font = new System.Drawing.Font("MS UI Gothic", 90F, System.Drawing.FontStyle.Bold);
            this.HandNmLb.Location = new System.Drawing.Point(12, 28);
            this.HandNmLb.Name = "HandNmLb";
            this.HandNmLb.Size = new System.Drawing.Size(633, 120);
            this.HandNmLb.TabIndex = 0;
            this.HandNmLb.Text = "Hand No.00";
            this.HandNmLb.Click += new System.EventHandler(this.HandNmLb_Click);
            // 
            // countLb
            // 
            this.countLb.AutoSize = true;
            this.countLb.Font = new System.Drawing.Font("MS UI Gothic", 110F, System.Drawing.FontStyle.Bold);
            this.countLb.Location = new System.Drawing.Point(88, 312);
            this.countLb.Name = "countLb";
            this.countLb.Size = new System.Drawing.Size(454, 147);
            this.countLb.TabIndex = 1;
            this.countLb.Text = "1 / 20";
            this.countLb.Click += new System.EventHandler(this.countLb_Click);
            // 
            // TimeLb
            // 
            this.TimeLb.AutoSize = true;
            this.TimeLb.Font = new System.Drawing.Font("MS UI Gothic", 100F, System.Drawing.FontStyle.Bold);
            this.TimeLb.Location = new System.Drawing.Point(118, 165);
            this.TimeLb.Name = "TimeLb";
            this.TimeLb.Size = new System.Drawing.Size(424, 134);
            this.TimeLb.TabIndex = 2;
            this.TimeLb.Text = "50.0秒";
            this.TimeLb.Click += new System.EventHandler(this.TimeLb_Click);
            // 
            // MeasurementInfo
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(14F, 24F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(645, 458);
            this.Controls.Add(this.TimeLb);
            this.Controls.Add(this.countLb);
            this.Controls.Add(this.HandNmLb);
            this.Font = new System.Drawing.Font("MS UI Gothic", 18F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(128)));
            this.Margin = new System.Windows.Forms.Padding(7, 6, 7, 6);
            this.Name = "MeasurementInfo";
            this.Text = "MeasurementInfo";
            this.Load += new System.EventHandler(this.MeasurementInfo_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label HandNmLb;
        private System.Windows.Forms.Label countLb;
        private System.Windows.Forms.Label TimeLb;
    }
}