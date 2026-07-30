using Newtonsoft.Json;

namespace HandGestureHomeControl
{
    /// <summary>
    /// Pythonへ送信するファイル出力要求
    /// </summary>
    public class DataExportRequest
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("transfer_id")]
        public string TransferId { get; set; }

        [JsonProperty("file_name")]
        public string FileName { get; set; }

        [JsonProperty("transfer_port")]
        public int TransferPort { get; set; }
    }

    /// <summary>
    /// Port6005の先頭で送られてくる転送情報
    /// </summary>
    public class FileTransferHeader
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("transfer_id")]
        public string TransferId { get; set; }

        [JsonProperty("file_name")]
        public string FileName { get; set; }

        [JsonProperty("compression")]
        public string Compression { get; set; }

        [JsonProperty("original_size")]
        public long OriginalSize { get; set; }
    }

    /// <summary>
    /// Windows側で待機中のファイル転送
    /// </summary>
    /// 
    /// <summary>
    /// Pythonへ送信する計測開始要求
    /// </summary>
    public class ExperimentStartRequest
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("trial_id")]
        public int TrialId { get; set; }
    }

    /// <summary>
    /// Pythonへ送信する計測中止要求
    /// </summary>
    public class ExperimentAbortRequest
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("trial_id")]
        public int TrialId { get; set; }
    }

    public class PendingFileTransfer
    {
        /// <summary>
        /// 転送ID
        /// </summary>
        public string TransferId { get; set; }

        /// <summary>
        /// 保存先ファイルパス
        /// </summary>
        public string FilePath { get; set; }

        /// <summary>
        /// 受信予定のファイルサイズ
        /// </summary>
        public long FileSize { get; set; }

        /// <summary>
        /// 現在までに受信したサイズ
        /// </summary>
        public long ReceivedSize { get; set; }

        /// <summary>
        /// ファイル名
        /// </summary>
        public string FileName { get; set; }
    }
}