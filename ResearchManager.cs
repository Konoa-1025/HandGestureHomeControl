using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using static HandGestureDashboard.Form1;

namespace HandGestureDashboard
{
    //==============================================================
    // 研究JSON解析
    //==============================================================
    public static class ResearchManager
    {
        public static bool TryParse(
            string json,
            out ResearchData researchData)
        {
            researchData = null;

            if (string.IsNullOrWhiteSpace(json))
            {
                return false;
            }

            try
            {
                JObject root =
                    JObject.Parse(json);

                //==================================================
                // type/dataで包まれている形式
                //==================================================
                JToken dataToken =
                    root["data"];

                if (dataToken != null &&
                    dataToken.Type == JTokenType.Object)
                {
                    researchData =
                        dataToken.ToObject<ResearchData>();

                    return researchData != null;
                }

                //==================================================
                // ResearchDataが直接送られている形式
                //==================================================
                researchData =
                    root.ToObject<ResearchData>();

                return researchData != null;
            }
            catch (JsonReaderException)
            {
                return false;
            }
            catch (JsonSerializationException)
            {
                return false;
            }

        }

        public static List<MeasurementStep> LoadMeasurementCsv(string csvPath)
        {
            List<MeasurementStep> steps = new List<MeasurementStep>();

            if (!File.Exists(csvPath))
            {
                throw new FileNotFoundException("CSVファイルが見つかりません。", csvPath);
            }

            string[] lines = File.ReadAllLines(csvPath);

            // 1行目はヘッダーなので2行目から読む
            for (int i = 1; i < lines.Length; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i]))
                    continue;

                string[] cols = lines[i].Split(',');

                if (cols.Length < 4)
                    continue;

                if (!int.TryParse(cols[0], out int handNumber))
                    continue;

                if (!double.TryParse(
                    cols[1],
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out double holdTime))
                    continue;

                MeasurementStep step = new MeasurementStep
                {
                    HandNumber = handNumber,
                    HoldTime = holdTime,
                    Gesture = cols[2].Trim(),
                    Direction = cols[3].Trim()
                };

                steps.Add(step);
            }

            _measurementSteps = steps;

            return _measurementSteps;
        }
        private static List<MeasurementStep> _measurementSteps =
    new List<MeasurementStep>();

        public static IReadOnlyList<MeasurementStep> MeasurementSteps
        {
            get { return _measurementSteps; }
        }

        public static int StepCount
        {
            get { return _measurementSteps.Count; }
        }

        public static MeasurementStep GetStep(int index)
        {
            if (index < 0 || index >= _measurementSteps.Count)
                return null;

            return _measurementSteps[index];
        }
    }
}