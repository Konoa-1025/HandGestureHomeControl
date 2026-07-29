using System;
using Newtonsoft.Json;

namespace HandGestureDashboard
{
    //==============================================================
    // Port1から受信する研究データ全体
    //==============================================================
    public class ResearchData
    {
        [JsonProperty("timestamp")]
        public DateTimeOffset Timestamp { get; set; }

        [JsonProperty("elapsed_ms")]
        public double ElapsedMs { get; set; }

        [JsonProperty("frame_id")]
        public long FrameId { get; set; }

        [JsonProperty("experiment")]
        public ExperimentData Experiment { get; set; }

        [JsonProperty("system")]
        public SystemData System { get; set; }

        [JsonProperty("performance")]
        public PerformanceData Performance { get; set; }

        [JsonProperty("model")]
        public ModelData Model { get; set; }

        [JsonProperty("recognition")]
        public RecognitionData Recognition { get; set; }
    }

    //==============================================================
    // 実験条件
    //==============================================================
    public class ExperimentData
    {
        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("trial_id")]
        public int TrialId { get; set; }

        [JsonProperty("expected_gesture")]
        public string ExpectedGesture { get; set; }

        [JsonProperty("brightness_percent")]
        public double BrightnessPercent { get; set; }

        [JsonProperty("distance_m")]
        public double DistanceM { get; set; }

        [JsonProperty("angle_degrees")]
        public double AngleDegrees { get; set; }

        [JsonProperty("background")]
        public string Background { get; set; }
    }

    //==============================================================
    // CPU・GPU・メモリ
    //==============================================================
    public class SystemData
    {
        [JsonProperty("cpu_percent")]
        public double CpuPercent { get; set; }

        // nullが来る可能性があるためnullable
        [JsonProperty("gpu_percent")]
        public double? GpuPercent { get; set; }

        [JsonProperty("memory_percent")]
        public double MemoryPercent { get; set; }
    }

    //==============================================================
    // FPS・映像遅延
    //==============================================================
    public class PerformanceData
    {
        [JsonProperty("fps")]
        public double Fps { get; set; }

        // nullが来る可能性があるためnullable
        [JsonProperty("video_latency_ms")]
        public double? VideoLatencyMs { get; set; }
    }

    //==============================================================
    // 使用モデル
    //==============================================================
    public class ModelData
    {
        [JsonProperty("current")]
        public string Current { get; set; }
    }

    //==============================================================
    // 認識結果
    //==============================================================
    public class RecognitionData
    {
        [JsonProperty("hand_detected")]
        public bool HandDetected { get; set; }

        [JsonProperty("raw_gesture")]
        public string RawGesture { get; set; }

        [JsonProperty("stable_gesture")]
        public string StableGesture { get; set; }
    }
}
