using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace HandGestureDashboard
{
    public class ExperimentPrepareRequest
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("data")]
        public ExperimentPrepareData Data { get; set; }
    }

    public class ExperimentPrepareData
    {
        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("trial_id")]
        public int TrialId { get; set; }

        [JsonProperty("brightness_percent")]
        public int BrightnessPercent { get; set; }

        [JsonProperty("distance_cm")]
        public int DistanceCm { get; set; }

        [JsonProperty("angle_degrees")]
        public int AngleDegrees { get; set; }

        [JsonProperty("background")]
        public string Background { get; set; }

        [JsonProperty("csv_file_name")]
        public string CsvFileName { get; set; }

        [JsonProperty("csv_content")]
        public string CsvContent { get; set; }
    }

    public class ExperimentPrepareResponse
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }

    public class DataListResponse
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("count")]
        public int Count { get; set; }

        [JsonProperty("files")]
        public List<string> Files { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }

    public class DataInfoResponse
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("data")]
        public DataInfo Data { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }

    public class DataInfo
    {
        [JsonProperty("file_name")]
        public string FileName { get; set; }

        [JsonProperty("experiment_id")]
        public string ExperimentId { get; set; }

        [JsonProperty("timestamp")]
        public string Timestamp { get; set; }
    }

    public partial class Form1
    {
        private readonly Dictionary<int, StreamWriter> _tcpWriters =
            new Dictionary<int, StreamWriter>();

        private readonly object _writerLock = new object();

        private TaskCompletionSource<ExperimentPrepareResponse>
            _prepareResponseSource;

        private void SelectCsvFile()
        {
            using (OpenFileDialog dialog = new OpenFileDialog())
            {
                dialog.Filter = "CSVファイル (*.csv)|*.csv";
                dialog.Title = "CSVファイルを選択";
                dialog.Multiselect = false;
                dialog.CheckFileExists = true;

                if (dialog.ShowDialog() != DialogResult.OK)
                    return;

                string csvPath = dialog.FileName;

                button7.Text = Path.GetFileName(csvPath);
                button7.Tag = csvPath;

                AppendLog("CSVファイルを選択しました: " + csvPath);
            }
        }

        private string ReadCsvContent(string csvPath)
        {
            if (string.IsNullOrWhiteSpace(csvPath))
                throw new ArgumentException("CSVファイルのパスが空です。");

            if (!File.Exists(csvPath))
                throw new FileNotFoundException("CSVファイルが見つかりません。", csvPath);

            using (StreamReader reader = new StreamReader(
                csvPath,
                Encoding.UTF8,
                true))
            {
                return reader.ReadToEnd();
            }
        }

        private async Task<bool> SendJsonToPortAsync(int port, object data)
        {
            AppendLog($"Port {port}: JSON送信処理開始");

            StreamWriter writer;

            lock (_writerLock)
            {
                _tcpWriters.TryGetValue(port, out writer);
            }

            if (writer == null)
            {
                AppendLog($"Port {port}: Writerが登録されていません。");
                return false;
            }

            try
            {
                string json = JsonConvert.SerializeObject(
                    data,
                    Formatting.None
                );

                AppendLog(
                    $"Port {port}: {Encoding.UTF8.GetByteCount(json)}バイト送信"
                );

                await writer.WriteLineAsync(json);
                await writer.FlushAsync();

                AppendLog($"Port {port}: JSON送信完了");
                AppendPortLog(port, "送信: " + json);

                return true;
            }
            catch (Exception ex)
            {
                AppendLog(
                    $"Port {port}: JSON送信失敗: " +
                    ex.GetType().Name + " / " + ex.Message
                );

                return false;
            }
        }

        private void OpenMeasurementForms()
        {
            if (handForm == null || handForm.IsDisposed)
            {
                handForm = new Hand();
                handForm.FormClosed += (s, args) => handForm = null;
                handForm.Show();
            }

            if (directionForm == null || directionForm.IsDisposed)
            {
                directionForm = new Direction();
                directionForm.FormClosed += (s, args) => directionForm = null;
                directionForm.Show();
            }

            if (cameraForm == null || cameraForm.IsDisposed)
            {
                cameraForm = new Camera();
                cameraForm.FormClosed += (s, args) => cameraForm = null;
                cameraForm.Show();
            }
        }

        private void ResetMeasurementPreparation(string message)
        {
            DataPushTimer.Stop();
            CountDown.Stop();
            label9.Text = "";

            StartPushBt.Text = "計測準備";
            StartPushBt.BackColor = Color.FromArgb(128, 192, 255);
            StartPushBt.Enabled = true;
            tableLayoutPanel4.Enabled = true;

            count = 8;

            if (!string.IsNullOrWhiteSpace(message))
                AppendLog(message);
        }

        private void CompleteMeasurementPreparation()
        {
            DataPushTimer.Stop();
            label9.Text = "送信完了";

            StartPushBt.Text = "計測開始";
            StartPushBt.BackColor = Color.FromArgb(128, 255, 128);
            StartPushBt.Enabled = true;
            tableLayoutPanel4.Enabled = false;

            AppendLog("計測準備が完了しました。");
        }

        private async Task PrepareExperimentAsync()
        {
            if (string.IsNullOrWhiteSpace(exNamebx.Text))
            {
                ResetMeasurementPreparation("実験名を入力してください。");
                return;
            }

            if (button7.Tag == null)
            {
                ResetMeasurementPreparation("CSVファイルを選択してください。");
                return;
            }

            int trialId;
            if (!int.TryParse(label34.Text, out trialId))
            {
                ResetMeasurementPreparation("試行番号が正しくありません。");
                return;
            }

            string csvPath = button7.Tag.ToString();
            string csvContent;

            try
            {
                csvContent = ReadCsvContent(csvPath);
            }
            catch (Exception ex)
            {
                ResetMeasurementPreparation("CSV読込失敗: " + ex.Message);
                return;
            }

            if (string.IsNullOrWhiteSpace(csvContent))
            {
                ResetMeasurementPreparation("CSVファイルの中身が空です。");
                return;
            }

            OpenMeasurementForms();

            ExperimentPrepareRequest request = new ExperimentPrepareRequest
            {
                Type = "experiment_prepare",
                Data = new ExperimentPrepareData
                {
                    ExperimentId = exNamebx.Text.Trim(),
                    TrialId = trialId,

                    // 実際のコントロール名に置き換えること
                    BrightnessPercent = (int)brightnessNumericUpDown.Value,
                    DistanceCm = (int)distanceNumericUpDown.Value,
                    AngleDegrees = (int)angleNumericUpDown.Value,
                    Background = backgroundComboBox.Text,

                    CsvFileName = Path.GetFileName(csvPath),
                    CsvContent = csvContent
                }
            };

            AppendLog("環境データとCSV全文を送信します。");

            tableLayoutPanel4.Enabled = false;
            StartPushBt.Enabled = false;
            DataPushTimer.Start();

            _prepareResponseSource =
                new TaskCompletionSource<ExperimentPrepareResponse>();

            bool sent = await SendJsonToPortAsync(
                Properties.Settings.Default.port4,
                request
            );

            if (!sent)
            {
                _prepareResponseSource = null;
                ResetMeasurementPreparation("環境データの送信に失敗しました。");
                return;
            }

            Task completedTask = await Task.WhenAny(
                _prepareResponseSource.Task,
                Task.Delay(10000)
            );

            if (completedTask != _prepareResponseSource.Task)
            {
                _prepareResponseSource = null;
                ResetMeasurementPreparation("返信がないため計測準備に失敗しました。");
                return;
            }

            ExperimentPrepareResponse response =
                await _prepareResponseSource.Task;

            _prepareResponseSource = null;

            if (response == null || !response.Success)
            {
                string errorMessage = response?.Message ?? "不明なエラーが発生しました。";
                ResetMeasurementPreparation("計測準備失敗: " + errorMessage);
                return;
            }

            SaveExperimentHistory(exNamebx.Text.Trim(), trialId);
            CompleteMeasurementPreparation();

            AppendLog("計測端末: " + (response.Message ?? "準備完了"));
        }

        private bool TryHandlePrepareResponse(string json)
        {
            try
            {
                JObject root = JObject.Parse(json);
                string type = root["type"]?.ToString();

                if (type != "experiment_prepare_result")
                    return false;

                ExperimentPrepareResponse response =
                    root.ToObject<ExperimentPrepareResponse>();

                _prepareResponseSource?.TrySetResult(response);
                return true;
            }
            catch (JsonException ex)
            {
                AppendPortLog(
                    Properties.Settings.Default.port4,
                    "計測準備返信JSON解析失敗: " + ex.Message
                );
                return true;
            }
        }

        private void RegisterTcpWriter(int port, StreamWriter writer)
        {
            lock (_writerLock)
            {
                _tcpWriters[port] = writer;
            }
            AppendLog($"Port {port}: 送信用Writerを登録しました。");
        }

        private void UnregisterTcpWriter(int port, StreamWriter writer)
        {
            lock (_writerLock)
            {
                StreamWriter currentWriter;

                if (_tcpWriters.TryGetValue(port, out currentWriter) &&
                    ReferenceEquals(currentWriter, writer))
                {
                    _tcpWriters.Remove(port);
                }
            }
        }

        private bool TryHandleDataListResponse(
    string json)
        {
            try
            {
                JObject root = JObject.Parse(json);

                if (root["type"]?.ToString()
                    != "data_list_result")
                {
                    return false;
                }

                DataListResponse response =
                    root.ToObject<DataListResponse>();

                BeginInvoke(new Action(() =>
                {
                    listBox1.Items.Clear();

                    if (response == null ||
                        !response.Success)
                    {
                        AppendLog(
                            response?.Message
                            ?? "ファイル一覧取得に失敗しました。"
                        );

                        return;
                    }

                    if (response.Files != null)
                    {
                        foreach (string fileName
                            in response.Files)
                        {
                            listBox1.Items.Add(fileName);
                        }
                    }

                    AppendLog(
                        $"JSONファイルを{response.Count}件取得しました。"
                    );
                }));

                return true;
            }
            catch (JsonException ex)
            {
                AppendLog(
                    "ファイル一覧JSON解析失敗: "
                    + ex.Message
                );

                return true;
            }
        }

        private bool TryHandleDataInfoResponse(
    string json)
        {
            try
            {
                JObject root = JObject.Parse(json);

                if (root["type"]?.ToString()
                    != "data_info_result")
                {
                    return false;
                }

                DataInfoResponse response =
                    root.ToObject<DataInfoResponse>();

                BeginInvoke(new Action(() =>
                {
                    if (response == null ||
                        !response.Success ||
                        response.Data == null)
                    {
                        AppendLog(
                            response?.Message
                            ?? "ファイル情報取得に失敗しました。"
                        );

                        return;
                    }

                    fileNameLabel.Text =
                        response.Data.FileName;

                    experimentIdLabel.Text =
                        response.Data.ExperimentId;

                    timestampLabel.Text =
                        response.Data.Timestamp;

                    AppendLog(
                        $"データ情報を取得しました: " +
                        response.Data.FileName
                    );
                }));

                return true;
            }
            catch (JsonException ex)
            {
                AppendLog(
                    "ファイル情報JSON解析失敗: "
                    + ex.Message
                );

                return true;
            }
        }
    }
}
