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

/**
 * Print slip handler with proper preview support
 * Opens slip in a hidden window, loads it, then triggers print dialog
 * The print dialog allows user to preview before printing or save as PDF
 */
ipcMain.on('print-slip', (event, slipId) => {
    const printWindow = new BrowserWindow({
        width: 800,
        height: 1100,
        show: false,  // Hidden until loaded
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false
        }
    });

    printWindow.loadURL(`http://localhost:5000/print/${slipId}`);

    printWindow.webContents.on('did-finish-load', () => {
        // Wait for content to render, then show print dialog
        setTimeout(() => {
            // Show the window briefly for better UX (optional)
            // printWindow.show();

            // Open print dialog with preview enabled
            printWindow.webContents.print({
                silent: false,  // Show print dialog
                printBackground: true,  // Print background colors and images
                color: true,  // Color printing
                margin: {
                    marginType: 'printableArea'
                },
                landscape: false,
                pagesPerSheet: 1,
                collate: false,
                copies: 1
            }, (success, errorType) => {
                if (!success && errorType) {
                    console.error('Print failed:', errorType);
                }
                // Close print window after print dialog is closed
                printWindow.close();
            });
        }, 1500);  // Increased timeout to ensure full render
    });

    // Handle print window errors
    printWindow.webContents.on('did-fail-load', () => {
        console.error('Failed to load print content');
        printWindow.close();
    });
});
