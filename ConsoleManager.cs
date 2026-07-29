using System;

namespace HandGestureDashboard
{
    public enum ConsoleCommandType
    {
        Message,
        Clear,
        Exit,
        Save,
        TcpStart,
        TcpStop,
        TcpList,
        TcpEdit,
        PowerShell,
        IP
    }

    public class ConsoleCommandResult
    {
        public ConsoleCommandType Type { get; set; }

        public string Message { get; set; }

        public int PortIndex { get; set; }

        public int PortNumber { get; set; }

        public string Command { get; set; }
    }

    public class ConsoleManager
    {
        public ConsoleCommandResult Execute(string command)
        {
            command = command.Trim();

            if (string.IsNullOrWhiteSpace(command))
            {
                return CreateMessage("");
            }

            string[] args = command.Split(
                new char[] { ' ' },
                StringSplitOptions.RemoveEmptyEntries
            );

            string cmd = args[0].ToLower();

            switch (cmd)
            {
                case "help":
                    return CreateMessage(
                        "help    : コマンド一覧\n" +
                        "clear   : コンソールを消去\n" +
                        "status  : システム状態\n" +
                        "time    : 現在時刻\n" +
                        "exit    : アプリケーションを終了\n" +
                        "save    : 設定を保存\n" +
                        "shell [command] : PowerShellを実行\n" +
                        "tcp start\n" +
                        "tcp stop\n" +
                        "tcp list\n" +
                        "tcp edit port0 6001"
                    );

                case "clear":
                    return CreateResult(ConsoleCommandType.Clear);

                case "exit":
                    return CreateResult(ConsoleCommandType.Exit);

                case "save":
                    return CreateResult(ConsoleCommandType.Save);

                case "ip":
                    return CreateResult(ConsoleCommandType.IP);

                case "status":
                    return CreateMessage("System: Ready");

                case "time":
                    return CreateMessage(
                        DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
                    );

                case "tcp":
                    return ExecuteTcp(args);

                case "shell":
                    return ExecutePowerShell(command, args);

                default:
                    return CreateMessage(
                        "Unknown command: " + command
                    );
            }
        }

        private ConsoleCommandResult ExecutePowerShell(
            string originalCommand,
            string[] args)
        {
            if (args.Length < 2)
            {
                return CreateMessage(
                    "PowerShellコマンドが指定されていません。\n" +
                    "使用法: shell ipconfig"
                );
            }

            string powerShellCommand =
                originalCommand.Substring(args[0].Length).Trim();

            return new ConsoleCommandResult
            {
                Type = ConsoleCommandType.PowerShell,
                Command = powerShellCommand,
                Message = ""
            };
        }

        private ConsoleCommandResult ExecuteTcp(string[] args)
        {
            if (args.Length < 2)
            {
                return CreateMessage(
                    "使用法: tcp [start|stop|list|edit]"
                );
            }

            switch (args[1].ToLower())
            {
                case "start":
                    return CreateResult(
                        ConsoleCommandType.TcpStart
                    );

                case "stop":
                    return CreateResult(
                        ConsoleCommandType.TcpStop
                    );

                case "list":
                    return CreateResult(
                        ConsoleCommandType.TcpList
                    );

                case "edit":
                    return ExecuteTcpEdit(args);

                default:
                    return CreateMessage(
                        "Unknown TCP command: " + args[1]
                    );
            }
        }

        private ConsoleCommandResult ExecuteTcpEdit(string[] args)
        {
            if (args.Length < 4)
            {
                return CreateMessage(
                    "使用法: tcp edit port0 6001"
                );
            }

            int portIndex;

            switch (args[2].ToLower())
            {
                case "port0":
                    portIndex = 0;
                    break;

                case "port1":
                    portIndex = 1;
                    break;

                case "port2":
                    portIndex = 2;
                    break;

                case "port3":
                    portIndex = 3;
                    break;

                case "port4":
                    portIndex = 4;
                    break;

                case "port5":
                    portIndex = 5;
                    break;

                default:
                    return CreateMessage(
                        "存在しないポートです: " + args[2]
                    );
            }

            int portNumber;

            if (!int.TryParse(args[3], out portNumber))
            {
                return CreateMessage(
                    "ポート番号は数値で指定してください。"
                );
            }

            if (portNumber < 1 || portNumber > 65535)
            {
                return CreateMessage(
                    "ポート番号は1～65535で指定してください。"
                );
            }

            return new ConsoleCommandResult
            {
                Type = ConsoleCommandType.TcpEdit,
                PortIndex = portIndex,
                PortNumber = portNumber
            };
        }

        private ConsoleCommandResult CreateResult(
            ConsoleCommandType type)
        {
            return new ConsoleCommandResult
            {
                Type = type,
                Message = "",
                Command = ""
            };
        }

        private ConsoleCommandResult CreateMessage(string message)
        {
            return new ConsoleCommandResult
            {
                Type = ConsoleCommandType.Message,
                Message = message,
                Command = ""
            };
        }
    }
}