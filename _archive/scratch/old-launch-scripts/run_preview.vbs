Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

repo = fso.GetParentFolderName(WScript.ScriptFullName)
compiled = repo & "\compiled_scene.json"
venvPy = repo & "\.venv\Scripts\python.exe"

If fso.FileExists(venvPy) Then
  cmd = Chr(34) & venvPy & Chr(34) & " -m Graphics.Animations.tools.runtime_player " & _
        Chr(34) & compiled & Chr(34) & " --fps 14 --duration 10 --overlay --noinput"
Else
  cmd = "py -m Graphics.Animations.tools.runtime_player " & _
        Chr(34) & compiled & Chr(34) & " --fps 14 --duration 10 --overlay --noinput"
End If

' 0 means window hidden; 1 shows window; True waits for completion
sh.Run cmd, 1, True



