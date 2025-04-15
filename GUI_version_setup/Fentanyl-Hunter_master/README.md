# Fentanyl-Hunter

Fentanyl Hunter is a desktop application specialized for screening and annotation of fentanyl-related compounds. This platform is capable of identifying fentanyl, its analogues, and metabolites in both biological and environmental samples.

## Prerequisites

Before building the application, ensure you have the following installed:

- Node.js (v16+)
- npm (v8+)
- Electron (installed via npm)
- electron-builder (installed via npm)

## Building the Frontend Application

Follow these steps to build the Fentanyl Hunter desktop application:

1. Clone the repository and navigate to the project directory
   ```bash
   git clone https://github.com/FangLabNTU/GUI_version_setup. git
   cd fentanyl-hunter
   ```

2. Install dependencies
   ```bash
   npm install
   ```

3. Build the application
   ```bash
   # Option 1: Build for production (creates a distributable package)
   npm run electron:build
   
   # Option 2: Build just the Vue application (without Electron packaging)
   npm run build
   ```

4. Locate the built application
   - The packaged application will be available in the `electron-dist` directory
   - You'll find the installer file `Fentanyl Hunter Setup x.x.x.exe` for Windows

## Additional Build Configuration

The build configuration is defined in the `build` section of `package.json`:

```json
"build": {
  "appId": "com.fentanyl.app",
  "productName": "Fentanyl Hunter",
  "directories": {
    "output": "electron-dist"
  },
  "win": {
    "target": ["nsis"],
    "icon": "public/icon.ico"
  },
  "files": [
    "dist/**/*",
    "electron/**/*"
  ]
}
```

You can modify these settings to adjust the build output if needed.

## Running in Development Mode

If you want to test the application before building:

```bash
# Run in development mode
npm run electron:dev
```

## Troubleshooting Build Issues

- Ensure all dependencies are correctly installed
- Check that Node.js and npm versions are compatible
- Verify that the project directory has proper write permissions
- For specific error messages, consult the electron-builder documentation

## License

[MIT](LICENSE)
