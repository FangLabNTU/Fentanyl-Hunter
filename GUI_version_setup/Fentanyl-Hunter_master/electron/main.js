const { app, BrowserWindow, ipcMain, dialog, globalShortcut } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    icon: path.join(__dirname, '../public/icon.ico'),
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      devTools: true
    }
  })

  win.setMenu(null)

  if (process.env.NODE_ENV === 'development') {
    win.webContents.openDevTools()
  }

  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  win.webContents.on('context-menu', (e, params) => {
    if (params.isEditable || params.inputFieldType !== 'none') {
      const menu = require('electron').Menu.buildFromTemplate([
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { type: 'separator' },
        {
          label: 'Inspect Element',
          click: () => {
            win.webContents.inspectElement(params.x, params.y)
          }
        }
      ])
      menu.popup()
    }
  })

  ipcMain.handle('select-file', async (event, options) => {
    const result = await dialog.showOpenDialog(win, {
      properties: ['openFile'],
      filters: options.filters || []
    })
    return result.filePaths[0] || ''
  })

  ipcMain.handle('select-save-directory', async () => {
    const result = await dialog.showOpenDialog(win, {
      properties: ['openDirectory'],
      title: '选择保存目录'
    })
    return result.filePaths[0] || ''
  })

  ipcMain.handle('joinPath', (event, ...args) => {
    return path.join(...args)
  })
}

app.whenReady().then(() => {
  createWindow()

  globalShortcut.register('F12', () => {
    const win = BrowserWindow.getFocusedWindow()
    if (win) {
      win.webContents.toggleDevTools()
    }
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
}) 