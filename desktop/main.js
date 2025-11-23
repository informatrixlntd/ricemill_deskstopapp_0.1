const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        icon: path.join(__dirname, 'assets', 'icon.png'),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },
        autoHideMenuBar: true,
        resizable: true
    });

    mainWindow.loadFile(path.join(__dirname, 'login.html'));

    mainWindow.on('closed', function() {
        mainWindow = null;
    });
}

function startPythonBackend() {
    const pythonScript = path.join(__dirname, '..', 'backend', 'app.py');
    pythonProcess = spawn('python', [pythonScript], {
        cwd: path.join(__dirname, '..')
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });

    setTimeout(() => {
        console.log('Backend started successfully');
    }, 3000);
}

app.on('ready', () => {
    startPythonBackend();
    createWindow();
});

app.on('window-all-closed', function() {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function() {
    if (mainWindow === null) {
        createWindow();
    }
});

ipcMain.on('login-success', () => {
    mainWindow.loadFile(path.join(__dirname, 'app.html'));
});

ipcMain.on('logout', () => {
    mainWindow.loadFile(path.join(__dirname, 'login.html'));
});

ipcMain.on('print-slip', (event, slipId) => {
    const printWindow = new BrowserWindow({
        width: 800,
        height: 1100,
        show: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    printWindow.loadURL(`http://localhost:5000/print/${slipId}`);

    printWindow.webContents.on('did-finish-load', () => {
        setTimeout(() => {
            printWindow.webContents.print({
                silent: false,
                printBackground: true,
                deviceName: ''
            }, (success, errorType) => {
                if (!success) {
                    console.error('Print failed:', errorType);
                }
                printWindow.close();
            });
        }, 1000);
    });
});
