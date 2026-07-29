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
    public class PendingFileTransfer
    {
        public string TransferId { get; set; }

        public string FileName { get; set; }

        public string SavePath { get; set; }
    }
}