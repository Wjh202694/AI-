Option Explicit

Dim shell, fso, http
Dim pythonExe, projectDir, port, url
Dim cmdLine, waitMs

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = Left(WScript.ScriptFullName, Len(WScript.ScriptFullName) - Len(WScript.ScriptName))
pythonExe = shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

If Not fso.FileExists(pythonExe) Then
    MsgBox "Python not found:" & vbCrLf & pythonExe, vbCritical, "Souyi"
    WScript.Quit 1
End If

port = 8321
url = "http://127.0.0.1:" & port & "/"

Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http.setTimeouts 1000, 1000, 1000, 1000
On Error Resume Next
http.open "GET", "http://127.0.0.1:" & port & "/api/health", False
http.setRequestHeader "Connection", "close"
http.send
If Err.Number = 0 Then
    If http.status = 200 Then
        shell.Run url, 1, False
        WScript.Quit 0
    End If
End If
On Error Goto 0

cmdLine = Chr(34) & pythonExe & Chr(34) & " " & Chr(34) & projectDir & "main.py" & Chr(34)

shell.Run cmdLine, 0, False

waitMs = 0
Do While waitMs < 10000
    WScript.Sleep 500
    waitMs = waitMs + 500
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.setTimeouts 1000, 1000, 1000, 1000
    On Error Resume Next
    http.open "GET", "http://127.0.0.1:" & port & "/api/health", False
    http.setRequestHeader "Connection", "close"
    http.send
    If Err.Number = 0 Then
        If http.status = 200 Then
            On Error Goto 0
            Exit Do
        End If
    End If
    On Error Goto 0
Loop

shell.Run url, 1, False

WScript.Quit 0
