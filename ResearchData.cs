using System;
using System.Text.Json.Serialization;

namespace HandGestureDashboard
{
    //==============================================================
    // Port1から受信する研究データ全体
    //==============================================================
    public class ResearchData
    {
        [JsonPropertyName("timestamp")]
        public DateTimeOffset Timestamp { get; set; }

        [JsonPropertyName("elapsed_ms")]
        public double ElapsedMs { get; set; }

        [JsonPropertyName("frame_id")]
        public long FrameId { get; set; }

        [JsonPropertyName("experiment")]
        public ExperimentData Experiment { get; set; }

        [JsonPropertyName("system")]
        public SystemData System { get; set; }

        [JsonPropertyName("performance")]
        public PerformanceData Performance { get; set; }

        [JsonPropertyName("model")]
        public ModelData Model { get; set; }

        [JsonPropertyName("recognition")]
        public RecognitionData Recognition { get; set; }
    }

    //==============================================================
    // 実験条件
    //==============================================================
    public class ExperimentData
    {
        [JsonPropertyName("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonPropertyName("trial_id")]
        public int TrialId { get; set; }

        [JsonPropertyName("expected_gesture")]
        public string ExpectedGesture { get; set; }

        [JsonPropertyName("brightness_percent")]
        public double BrightnessPercent { get; set; }

        [JsonPropertyName("distance_m")]
        public double DistanceM { get; set; }

        [JsonPropertyName("angle_degrees")]
        public double AngleDegrees { get; set; }

        [JsonPropertyName("background")]
        public string Background { get; set; }
    }

    //==============================================================
    // CPU・GPU・メモリ
    //==============================================================
    public class SystemData
    {
        [JsonPropertyName("cpu_percent")]
        public double CpuPercent { get; set; }

        // JSONでnullが来るためnullable
        [JsonPropertyName("gpu_percent")]
        public double? GpuPercent { get; set; }

        [JsonPropertyName("memory_percent")]
        public double MemoryPercent { get; set; }
    }

    //==============================================================
    // FPS・映像遅延
    //==============================================================
    public class PerformanceData
    {
        [JsonPropertyName("fps")]
        public double Fps { get; set; }

        // JSONでnullが来るためnullable
        [JsonPropertyName("video_latency_ms")]
        public double? VideoLatencyMs { get; set; }
    }

    //==============================================================
    // 現在使用中のモデル
    //==============================================================
    public class ModelData
    {
        [JsonPropertyName("current")]
        public string Current { get; set; }
    }

    //==============================================================
    // 手・ジェスチャー認識結果
    //==============================================================
    public class RecognitionData
    {
        [JsonPropertyName("hand_detected")]
        public bool HandDetected { get; set; }

        [JsonPropertyName("raw_gesture")]
        public string RawGesture { get; set; }

        [JsonPropertyName("stable_gesture")]
        public string StableGesture { get; set; }
    }
}
