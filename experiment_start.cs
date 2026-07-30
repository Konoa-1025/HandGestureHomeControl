using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace HandGestureDashboard
{
    public class ExperimentStartRequest
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("trial_id")]
        public int TrialId { get; set; }
    }
    public class ExperimentAbortRequest
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("trial_id")]
        public int TrialId { get; set; }
    }
}
