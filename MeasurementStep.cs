using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace HandGestureDashboard
{
    public class MeasurementStep
    {
        public int HandNumber { get; set; }

        public double HoldTime { get; set; }

        public string Gesture { get; set; }

        public string Direction { get; set; }
    }
}
