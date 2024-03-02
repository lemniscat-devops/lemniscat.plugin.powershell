# lemniscat.plugin.powershell
A powershell plugin for lemniscat

## Description
This plugin allows you to run powershell commands and scripts in your lemniscat pipeline.

## Usage
### Pre-requisites
In order to use this plugin, you need to add plugin into the required section of your manifest file.

```yaml
requirements:
  - name: lemniscat.plugin.powershell
    version: 0.1.0
```

### Running powershell commands
```yaml
- task: powershell
  displayName: 'Powershell'
  steps:
    - run
  parameters:
    type: inline
    script: |
      $name = "Philippe"
      Write-Host "Hello $name"
```

### Running powershell script
```yaml
- task: powershell
  displayName: 'Powershell'
  steps:
    - run
  parameters:
    type: file
    filePath: ${{ workingdirectory }}/scripts/Hello.ps1
    fileParams:
      name: ${{ username }}
```
### Running powershell commmands and pass variables through json file
> [!NOTE] 
> This feature is particulary recommand when you need to manipulate complexe variable with your task.
> You can access to the variables in the json file by using the following command:
> ```powershell
> $location = Get-Location
> $variables = Get-Content "$($location.path)/vars.json" | ConvertFrom-Json -Depth 100
> ```

```yaml
- task: powershell
  displayName: 'Powershell'
  steps:
    - run
  parameters:
    type: inline
    script: |
      $location = Get-Location
      $variables = Get-Content "$($location.path)/vars.json" | ConvertFrom-Json -Depth 100
      $version = az --version
      Write-Host "Azure CLI version: $version"
    storeVariablesInFile:
      format: json
      withSecrets: false
```

## Inputs

### Parameters
- `type`: The type of the command to run. It can be `inline` or `file`
- `script`: The script to run. It can be a powershell command line. It is used only if `type` is `inline`
- `filePath`: The path of the powershell script file (*.ps1) to run. It is used only if `type` is `file`
- `fileParams`: The parameters to pass to the powershell script file. It is used only if `type` is `file`
- [`storeVariablesInFile`](#StoreVariablesInFile): Describe the way to store the variables in a file to used in the task.

#### StoreVariablesInFile
- `format`: The format of the file to store the variables. It can be `json` or `yaml`
- `withSecrets`: A boolean value to indicate if the secrets should be stored in the file. It can be `true` or `false`

## Outputs

You can push variables to the lemniscat runtime in order to be used after by other tasks.
To do that, you need to use `Write-Host` command in your powershell script to push variables to the lemniscat runtime.
You must use the following format to push variables to the lemniscat runtime:
`[lemniscat.pushvar] <variableName>=<variableValue>`

For example:
```powershell
Write-Host "[lemniscat.pushvar] workspaceExist=$workspaceExist"
```

You can specify the sensitivity of the variable by adding `secret` like this :
`[lemniscat.pushvar.secret] <variableName>=<variableValue>`

For example:
```powershell
Write-Host "[lemniscat.pushvar.secret] storageAccountKey=$storageAccountKey"
```