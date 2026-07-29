using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

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
    }
}