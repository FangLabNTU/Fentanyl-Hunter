const { contextBridge, ipcRenderer } = require('electron')
const path = require('path')

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  selectSaveDirectory: () => ipcRenderer.invoke('select-save-directory'),
  joinPath: (...args) => ipcRenderer.invoke('joinPath', ...args)
}) 