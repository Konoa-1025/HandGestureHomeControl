using System;

public class ConsoleManager
{
    public string Execute(string command)
    {
        command = command.Trim();

        if (string.IsNullOrEmpty(command))
        {
            return "";
        }

        switch (command.ToLower())
        {
            case "help":
                return "help, clear, status, time";

            case "status":
                return "System: Ready";

            case "time":
                return DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

            default:
                return $"Unknown command: {command}";
        }
    }
}