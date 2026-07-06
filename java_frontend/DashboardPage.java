import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.net.*;

public class DashboardPage extends JFrame {

    String email;
    JTextArea resultArea;
    File lastSelectedFile;

    JPanel sidePanel;
    boolean menuOpen = true;

    JLabel cam1StatusCard, cam2StatusCard, cam3StatusCard, cam4StatusCard;
    JLabel serverHealthLabel;

    Timer dashboardTimer;

    int previousTigerCount = 0;
    long lastPopupTime = 0;
    String lastAlertKey = "";

    // ✅ FIX: This flag stops the auto-refresh timer from overwriting
    // your video/photo detection result in the result area.
    // Set to true while detection is running, false when done.
    boolean detectionRunning = false;

    public DashboardPage(String email) {
        this.email = email;

        setTitle("Tiger Detection Dashboard");
        setSize(1180, 780);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(null);
        getContentPane().setBackground(new Color(245, 247, 250));

        JButton menuButton = new JButton("MENU");
        menuButton.setBounds(20, 15, 90, 38);
        styleTopButton(menuButton);
        add(menuButton);

        JLabel title = new JLabel("Tiger Detection Monitoring System");
        title.setFont(new Font("Segoe UI", Font.BOLD, 25));
        title.setForeground(new Color(0, 70, 130));
        title.setBounds(320, 15, 560, 40);
        add(title);

        JLabel welcome = new JLabel("Welcome, " + email);
        welcome.setFont(new Font("Segoe UI", Font.BOLD, 14));
        welcome.setBounds(850, 20, 170, 30);
        add(welcome);

        JButton accountBtn = new JButton("Account");
        accountBtn.setBounds(1015, 18, 75, 35);
        styleTopButton(accountBtn);
        add(accountBtn);

        JButton logoutBtn = new JButton("Logout");
        logoutBtn.setBounds(1095, 18, 75, 35);
        styleTopButton(logoutBtn);
        add(logoutBtn);

        accountBtn.addActionListener(e -> new AccountPage(email));

        logoutBtn.addActionListener(e -> {
            dispose();
            new LoginPage();
        });

        createSidePanel();
        add(sidePanel);

        addCameraPanel("CAM_1", 270, 90);
        addCameraPanel("CAM_2", 610, 90);
        addCameraPanel("CAM_3", 270, 300);
        addCameraPanel("CAM_4", 610, 300);

        resultArea = new JTextArea("Result: Waiting...");
        resultArea.setFont(new Font("Segoe UI", Font.BOLD, 14));
        resultArea.setEditable(false);
        resultArea.setLineWrap(true);
        resultArea.setWrapStyleWord(true);
        resultArea.setBackground(Color.WHITE);
        resultArea.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JScrollPane scroll = new JScrollPane(resultArea);
        scroll.setBounds(270, 510, 650, 150);
        add(scroll);

        cam1StatusCard = createCard("CAM_1<br>Stopped<br>Result: None<br>Frames: 0");
        cam1StatusCard.setBounds(945, 90, 190, 85);
        add(cam1StatusCard);

        cam2StatusCard = createCard("CAM_2<br>Stopped<br>Result: None<br>Frames: 0");
        cam2StatusCard.setBounds(945, 185, 190, 85);
        add(cam2StatusCard);

        cam3StatusCard = createCard("CAM_3<br>Stopped<br>Result: None<br>Frames: 0");
        cam3StatusCard.setBounds(945, 280, 190, 85);
        add(cam3StatusCard);

        cam4StatusCard = createCard("CAM_4<br>Stopped<br>Result: None<br>Frames: 0");
        cam4StatusCard.setBounds(945, 375, 190, 85);
        add(cam4StatusCard);

        serverHealthLabel = createCard("Server<br>Ready");
        serverHealthLabel.setBounds(945, 475, 190, 140);
        add(serverHealthLabel);

        JLabel status = new JLabel("Status: Ready");
        status.setFont(new Font("Segoe UI", Font.BOLD, 14));
        status.setBounds(270, 700, 400, 25);
        add(status);

        menuButton.addActionListener(e -> {
            menuOpen = !menuOpen;
            sidePanel.setVisible(menuOpen);
        });

        startAutoRefresh();

        // ===== AI Button =====
        JButton aiButton = new JButton("AI");
        aiButton.setBounds(1080, 650, 65, 65);
        aiButton.setBackground(new Color(0, 120, 215));
        aiButton.setForeground(Color.WHITE);
        aiButton.setFont(new Font("Segoe UI", Font.BOLD, 18));
        aiButton.setFocusPainted(false);
        aiButton.setBorder(BorderFactory.createLineBorder(Color.WHITE, 2));
        add(aiButton);

        aiButton.addActionListener(e -> new AIAssistantPage(this));

        setVisible(true);
    }

    void createSidePanel() {
        sidePanel = new JPanel();
        sidePanel.setLayout(null);
        sidePanel.setBounds(0, 65, 250, 680);
        sidePanel.setBackground(new Color(235, 240, 245));
        sidePanel.setBorder(BorderFactory.createLineBorder(new Color(200, 210, 220)));

        JLabel menuTitle = new JLabel("CONTROL MENU", SwingConstants.CENTER);
        menuTitle.setForeground(new Color(0, 70, 130));
        menuTitle.setFont(new Font("Segoe UI", Font.BOLD, 18));
        menuTitle.setBounds(0, 15, 250, 30);
        sidePanel.add(menuTitle);

        int y = 65;

        JButton uploadPhoto = addMenuButton("Upload Photo", y);
        y += 42;
        JButton uploadVideo = addMenuButton("Upload Video", y);
        y += 42;
        JButton preview = addMenuButton("Preview", y);
        y += 42;
        JButton cameraControl = addMenuButton("Camera Control", y);
        y += 42;
        JButton systemStatus = addMenuButton("System Status", y);
        y += 42;
        JButton alertManagement = addMenuButton("Alerts", y);
        y += 42;
        JButton analytics = addMenuButton("Analytics", y);
        y += 42;
        JButton reports = addMenuButton("Reports", y);
        y += 42;
        JButton capturedFrames = addMenuButton("Captured Frames", y);
        y += 42;
        JButton tigerScreenshots = addMenuButton("Tiger Screenshots", y);
        y += 42;
        JButton latestTiger = addMenuButton("Latest Tiger Image", y);
        y += 42;
        JButton cleanup = addMenuButton("Cleanup Storage", y);

        uploadPhoto.addActionListener(e -> chooseAndDetect("detect_photo"));
        uploadVideo.addActionListener(e -> chooseAndDetect("detect_video"));

        preview.addActionListener(e -> {
            if (lastSelectedFile == null) {
                JOptionPane.showMessageDialog(this, "First upload a photo or video.");
                return;
            }
            new FullScreenPreview(lastSelectedFile);
        });

        cameraControl.addActionListener(e -> new CameraControlPage(this));
        systemStatus.addActionListener(e -> systemStatusMenu());
        alertManagement.addActionListener(e -> new AlertManagementPage());
        analytics.addActionListener(e -> new AnalyticsPage());
        reports.addActionListener(e -> new ReportsPage());

        capturedFrames.addActionListener(e -> openCapturedFramesAndDetect());
        tigerScreenshots.addActionListener(e -> openFolder("../python_backend/saved_tigers"));
        latestTiger.addActionListener(e -> openLatestTigerImage());

        cleanup.addActionListener(e -> {
            String response = callGetApi("http://127.0.0.1:5000/cleanup_storage");
            resultArea.setText("Cleanup Storage:\n" + formatJson(response));
        });
    }

    void openCapturedFramesAndDetect() {
        JFileChooser chooser = new JFileChooser("../python_backend/captured_frames");
        chooser.setDialogTitle("Select Captured Frame for Detection");

        int option = chooser.showOpenDialog(this);

        if (option == JFileChooser.APPROVE_OPTION) {
            File selectedFrame = chooser.getSelectedFile();
            lastSelectedFile = selectedFrame;

            // ✅ FIX: Block auto-refresh from overwriting result
            detectionRunning = true;
            resultArea.setText("Processing selected captured frame...\nPlease wait...");

            new Thread(() -> {
                String response = ApiClient.sendFile("detect_photo", selectedFrame);

                String formatted = formatDetectionResult(response);
                String result = extractTextValue(response, "result");
                String message = extractTextValue(response, "message");
                String aiDecision = getAIDecision(result, message);

                SwingUtilities.invokeLater(() -> {
                    resultArea.setText(
                            formatted +
                                    "\n\n========== AI DECISION SUPPORT ==========\n\n" +
                                    aiDecision);

                    // ✅ FIX: Allow auto-refresh again after result is shown
                    detectionRunning = false;

                    if (isTigerDetected(response)) {
                        playAlarm();
                        JOptionPane.showMessageDialog(
                                this,
                                "TIGER DETECTED in captured frame!\nAlert Generated.",
                                "Tiger Alert",
                                JOptionPane.WARNING_MESSAGE);
                        showNotification(
                                "TIGER DETECTED!",
                                new Color(255, 245, 245),
                                new Color(180, 0, 0));
                    } else {
                        JOptionPane.showMessageDialog(
                                this,
                                "NO TIGER DETECTED in selected frame",
                                "Detection Result",
                                JOptionPane.INFORMATION_MESSAGE);
                        showNotification(
                                "NO TIGER DETECTED",
                                new Color(235, 255, 235),
                                new Color(0, 120, 0));
                    }
                });
            }).start();
        }
    }

    void addCameraPanel(String cameraId, int x, int y) {
        LiveVideoPanel cam = new LiveVideoPanel(cameraId);
        cam.setBounds(x, y, 310, 190);
        cam.setBorder(BorderFactory.createLineBorder(new Color(0, 105, 180), 2));
        add(cam);
    }

    void systemStatusMenu() {
        String camera = callGetApi("http://127.0.0.1:5000/camera_status");
        String health = callGetApi("http://127.0.0.1:5000/server_health");

        resultArea.setText(
                "===== CAMERA STATUS =====\n" + formatJson(camera) +
                        "\n\n===== SERVER HEALTH =====\n" + formatJson(health));
    }

    JButton addMenuButton(String text, int y) {
        JButton button = new JButton(text);
        button.setBounds(25, y, 200, 34);
        styleMenuButton(button);
        sidePanel.add(button);
        return button;
    }

    JLabel createCard(String text) {
        JLabel label = new JLabel("<html><center>" + text + "</center></html>", SwingConstants.CENTER);
        label.setOpaque(true);
        label.setBackground(Color.WHITE);
        label.setForeground(new Color(0, 70, 130));
        label.setFont(new Font("Segoe UI", Font.BOLD, 13));
        label.setBorder(BorderFactory.createLineBorder(new Color(0, 105, 180), 2));
        return label;
    }

    void startAutoRefresh() {
        dashboardTimer = new Timer(10000, e -> {
            updateCameraStatus();
            updateServerHealth();
        });
        dashboardTimer.start();
    }

    public void updateCameraStatus() {
        String response = callGetApi("http://127.0.0.1:5000/camera_status");

        updateOneCameraCard(cam1StatusCard, response, "CAM_1");
        updateOneCameraCard(cam2StatusCard, response, "CAM_2");
        updateOneCameraCard(cam3StatusCard, response, "CAM_3");
        updateOneCameraCard(cam4StatusCard, response, "CAM_4");

        // ✅ FIX: Only update the result area with camera status when
        // NO detection is currently running.
        // This prevents the auto-refresh from wiping your video/photo result.
        if (!detectionRunning) {
            updateResultAreaFromCameraStatus(response);
        }

        String tigerCountText = extractValue(response, "tiger_count");
        String lastResult = extractTextValue(response, "last_result");

        int currentTigerCount = parseIntSafe(tigerCountText, previousTigerCount);

        String alertKey = currentTigerCount + "_" + lastResult;
        long now = System.currentTimeMillis();

        if (currentTigerCount > previousTigerCount
                && !alertKey.equals(lastAlertKey)
                && now - lastPopupTime >= 10000) {

            playAlarm();

            JOptionPane.showMessageDialog(
                    this,
                    "🐅 Tiger Detected\n\nSighting Saved",
                    "Live Camera Alert",
                    JOptionPane.WARNING_MESSAGE);

            showNotification(
                    "🐅 Tiger Detected",
                    new Color(255, 245, 245),
                    new Color(180, 0, 0));

            lastPopupTime = now;
            lastAlertKey = alertKey;
        }

        previousTigerCount = currentTigerCount;
    }

    void updateOneCameraCard(JLabel card, String response, String camId) {
        String block = getCameraBlock(response, camId);

        String status = extractTextValue(block, "status");
        String result = extractTextValue(block, "last_result");
        String frames = extractValue(block, "frames_checked");

        if (status.equals(""))
            status = "Stopped";

        if (result.equals(""))
            result = "None";

        card.setText(
                "<html><center>" +
                        camId + "<br>" +
                        status + "<br>" +
                        "Result: " + result + "<br>" +
                        "Frames: " + frames +
                        "</center></html>");

        if (result.equalsIgnoreCase("Tiger")) {
            card.setForeground(new Color(180, 0, 0));
        } else if (status.equalsIgnoreCase("Online")) {
            card.setForeground(new Color(0, 125, 60));
        } else {
            card.setForeground(new Color(170, 20, 20));
        }
    }

    String getCameraBlock(String text, String camId) {
        try {
            int start = text.indexOf("\"" + camId + "\"");

            if (start == -1)
                return "";

            int nextCam = text.indexOf("\"CAM_", start + 6);

            if (nextCam == -1)
                return text.substring(start);

            return text.substring(start, nextCam);

        } catch (Exception e) {
            return "";
        }
    }

    // Pulls a nested JSON object's raw text, e.g. "sighting_classification": {...}
    // so extractTextValue() can then be run on just that inner block.
    String getObjectBlock(String text, String key) {
        try {
            int start = text.indexOf("\"" + key + "\"");

            if (start == -1)
                return "";

            int braceStart = text.indexOf("{", start);

            if (braceStart == -1)
                return "";

            int braceEnd = text.indexOf("}", braceStart);

            if (braceEnd == -1)
                return "";

            return text.substring(braceStart, braceEnd + 1);

        } catch (Exception e) {
            return "";
        }
    }

    void updateServerHealth() {
        String response = callGetApi("http://127.0.0.1:5000/server_health");
        serverHealthLabel.setText("<html><center>Server Health<br>" + formatJsonForHtml(response) + "</center></html>");
    }

    public String callGetApi(String apiUrl) {
        try {
            URL url = new URL(apiUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");

            BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            StringBuilder response = new StringBuilder();
            String line;

            while ((line = br.readLine()) != null)
                response.append(line).append("\n");

            br.close();
            return response.toString();

        } catch (Exception e) {
            return "Error: " + e.getMessage();
        }
    }

    public String callPostApi(String apiUrl, String data) {
        try {
            URL url = new URL(apiUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();

            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");

            OutputStream os = conn.getOutputStream();
            os.write(data.getBytes());
            os.flush();
            os.close();

            BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            StringBuilder response = new StringBuilder();
            String line;

            while ((line = br.readLine()) != null)
                response.append(line).append("\n");

            br.close();
            return response.toString();

        } catch (Exception e) {
            return "Error: " + e.getMessage();
        }
    }

    // ✅ FIXED chooseAndDetect — sets detectionRunning = true before the HTTP call
    // and detectionRunning = false AFTER the result is written to resultArea.
    //
    // WHAT YOU WILL SEE IN THE RESULT AREA after uploading a video:
    //
    // ========== DETECTION RESULT ==========
    // Result : Tiger Detected ← or No Tiger Detected
    // Frames Checked : 45
    // Tiger Frames : 8
    // Non-Tiger Frames : 37
    // Saved Image : C:\...\saved_tigers\tiger_20260628.jpg
    // PDF Report : C:\...\pdf_reports\report_20260628.pdf
    // Time : 28-06-2026 10:30 PM
    //
    // ========== AI DECISION ==========
    // [AI text from Ollama/Gemini here]
    //
    // ========== RAW SERVER RESPONSE ==========
    // [Full JSON from Flask]
    //
    // ========== AI DECISION SUPPORT ==========
    // [Second AI analysis]
    //
    // This result stays on screen permanently until you do another action.
    void chooseAndDetect(String action) {
        JFileChooser chooser = new JFileChooser();
        int option = chooser.showOpenDialog(this);

        if (option == JFileChooser.APPROVE_OPTION) {
            lastSelectedFile = chooser.getSelectedFile();

            String fileName = lastSelectedFile.getName().toLowerCase();
            boolean isVideo = fileName.endsWith(".mp4")
                    || fileName.endsWith(".avi")
                    || fileName.endsWith(".mov")
                    || fileName.endsWith(".mkv");

            if (isVideo) {
                new FullScreenPreview(lastSelectedFile);
            }

            // ✅ FIX: Block auto-refresh from overwriting result while processing
            detectionRunning = true;
            resultArea.setText("Processing...\nPlease wait. Detection is running...");

            new Thread(() -> {
                String response = ApiClient.sendFile(action, lastSelectedFile);

                System.out.println("=== RAW RESPONSE ===\n" + response + "\n=== END ===");
                String formatted = formatDetectionResult(response);

                String result = extractTextValue(response, "result");
                String message = extractTextValue(response, "message");
                String aiDecision = getAIDecision(result, message);

                SwingUtilities.invokeLater(() -> {
                    // Write the result first
                    resultArea.setText(
                            formatted +
                                    "\n\n========== AI DECISION SUPPORT ==========\n\n" +
                                    aiDecision);

                    // ✅ FIX: Only NOW allow auto-refresh to update the result area again
                    detectionRunning = false;

                    if (isTigerDetected(response)) {
                        playAlarm();
                        JOptionPane.showMessageDialog(
                                this,
                                "TIGER DETECTED!\nAlert Generated.",
                                "Tiger Alert",
                                JOptionPane.WARNING_MESSAGE);
                        showNotification(
                                "TIGER DETECTED!",
                                new Color(255, 245, 245),
                                new Color(180, 0, 0));
                    } else {
                        JOptionPane.showMessageDialog(
                                this,
                                "NO TIGER DETECTED",
                                "Detection Result",
                                JOptionPane.INFORMATION_MESSAGE);
                        showNotification(
                                "NO TIGER DETECTED",
                                new Color(235, 255, 235),
                                new Color(0, 120, 0));
                    }
                });
            }).start();
        }
    }

    String formatDetectionResult(String response) {
        String result = extractTextValue(response, "result");
        String message = extractTextValue(response, "message");
        String frames = extractValue(response, "frames_checked");
        String tigerFrames = extractValue(response, "tiger_frames");
        String nonTigerFrames = extractValue(response, "nontiger_frames");
        String savedImage = extractTextValue(response, "saved_image");
        String pdf = extractTextValue(response, "pdf_report");
        String aiDecisionText = extractTextValue(response, "ai_decision");
        String time = extractTextValue(response, "time");

        String identification = extractTextValue(response, "identification");
        String sightingStory = extractTextValue(response, "sighting_story");
        String classificationBlock = getObjectBlock(response, "sighting_classification");
        String activity = extractTextValue(classificationBlock, "activity");
        String risk = extractTextValue(classificationBlock, "risk");
        String timeContext = extractTextValue(classificationBlock, "time_context");

        String text = "========== DETECTION RESULT ==========\n\n";

        if (!message.equals(""))
            text += "Message        : " + message + "\n";

        if (!result.equals(""))
            text += "Result         : " + result + "\n";

        if (!frames.equals("0"))
            text += "Frames Checked : " + frames + "\n";

        if (!tigerFrames.equals("0"))
            text += "Tiger Frames   : " + tigerFrames + "\n";

        if (!nonTigerFrames.equals("0"))
            text += "Non-Tiger Frames : " + nonTigerFrames + "\n";

        if (!savedImage.equals(""))
            text += "Saved Image    : " + savedImage + "\n";

        if (!pdf.equals(""))
            text += "PDF Report     : " + pdf + "\n";

        if (!time.equals(""))
            text += "Time           : " + time + "\n";

        // ===== SIGHTING (shown right here in the result area — no separate button)
        // =====
        if (result.equalsIgnoreCase("Tiger Detected")) {
            text += "\n========== SIGHTING ==========\n";
            text += "Identification : " + (identification.equals("") ? "Not available" : identification) + "\n";
            text += "Activity       : " + (activity.equals("") ? "Unknown" : activity) + "\n";
            text += "Risk Level     : " + (risk.equals("") ? "Unknown" : risk) + "\n";
            text += "Time Context   : " + (timeContext.equals("") ? "Unknown" : timeContext) + "\n\n";
            text += "Sighting Story\n";
            text += (sightingStory.equals("") ? "Not available." : sightingStory) + "\n";
        } else {
            text += "\n========== SIGHTING ==========\n";
            text += (sightingStory.equals("")
                    ? "No tiger detected. No sighting recorded."
                    : sightingStory) + "\n";
        }

        if (!aiDecisionText.equals(""))
            text += "\n========== AI DECISION ==========\n" + aiDecisionText + "\n";

        text += "\n========== RAW SERVER RESPONSE ==========\n";
        text += formatJson(response);

        return text;
    }

    boolean isTigerDetected(String response) {
        String text = response.toLowerCase();

        if (text.contains("no tiger detected")) {
            return false;
        }

        if (text.contains("\"result\":\"tiger detected\"") ||
                text.contains("\"result\": \"tiger detected\"")) {
            return true;
        }

        if (text.contains("\"result\":\"tiger\"") ||
                text.contains("\"result\": \"tiger\"")) {
            return true;
        }

        if (text.contains("tiger detected")) {
            return true;
        }

        try {
            String tigerFramesVal = extractValue(response, "tiger_frames");
            int tigerFrames = Integer.parseInt(tigerFramesVal.trim());
            if (tigerFrames > 0) {
                return true;
            }
        } catch (Exception ignored) {
        }

        return false;
    }

    String formatJson(String json) {
        return json.replace("{", "{\n")
                .replace("}", "\n}")
                .replace(",", ",\n")
                .replace("\"", "");
    }

    String formatJsonForHtml(String json) {
        return json.replace("{", "")
                .replace("}", "")
                .replace(",", "<br>")
                .replace("\"", "")
                .trim();
    }

    void playAlarm() {
        new Thread(() -> {
            for (int i = 0; i < 3; i++) {
                Toolkit.getDefaultToolkit().beep();
                try {
                    Thread.sleep(300);
                } catch (Exception ignored) {
                }
            }
        }).start();
    }

    void openFolder(String path) {
        try {
            File folder = new File(path);

            if (!folder.exists())
                folder.mkdirs();

            Desktop.getDesktop().open(folder);

        } catch (Exception e) {
            JOptionPane.showMessageDialog(this, "Folder could not open");
        }
    }

    void openLatestTigerImage() {
        try {
            File latest = getLatestFile("../python_backend/saved_tigers");

            if (latest == null) {
                JOptionPane.showMessageDialog(this, "No tiger image saved yet");
                return;
            }

            Desktop.getDesktop().open(latest);

        } catch (Exception e) {
            JOptionPane.showMessageDialog(this, "Could not open latest tiger image");
        }
    }

    File getLatestFile(String folderPath) {
        File folder = new File(folderPath);
        File[] files = folder.listFiles();

        if (files == null || files.length == 0)
            return null;

        File latest = files[0];

        for (File file : files) {
            if (file.lastModified() > latest.lastModified())
                latest = file;
        }

        return latest;
    }

    String extractValue(String text, String key) {
        try {
            int index = text.indexOf(key);

            if (index == -1)
                return "0";

            int colon = text.indexOf(":", index);
            int comma = text.indexOf(",", colon);

            if (comma == -1)
                comma = text.indexOf("}", colon);

            if (comma == -1)
                comma = text.length();

            return text.substring(colon + 1, comma)
                    .replace("\"", "")
                    .replace("{", "")
                    .replace("}", "")
                    .trim();

        } catch (Exception e) {
            return "0";
        }
    }

    String extractTextValue(String text, String key) {
        try {
            int index = text.indexOf(key);

            if (index == -1)
                return "";

            int colon = text.indexOf(":", index);
            int comma = text.indexOf(",", colon);

            if (comma == -1)
                comma = text.indexOf("}", colon);

            if (comma == -1)
                comma = text.length();

            return text.substring(colon + 1, comma)
                    .replace("\"", "")
                    .replace("{", "")
                    .replace("}", "")
                    .trim();

        } catch (Exception e) {
            return "";
        }
    }

    int parseIntSafe(String value, int defaultValue) {
        try {
            return Integer.parseInt(value.trim());
        } catch (Exception e) {
            return defaultValue;
        }
    }

    double parseDoubleSafe(String value, double defaultValue) {
        try {
            return Double.parseDouble(value.trim());
        } catch (Exception e) {
            return defaultValue;
        }
    }

    String encode(String text) {
        try {
            return URLEncoder.encode(text, "UTF-8");
        } catch (Exception e) {
            return text;
        }
    }

    void showNotification(String message, Color background, Color foreground) {
        JWindow notification = new JWindow();

        JLabel label = new JLabel(message, SwingConstants.CENTER);
        label.setOpaque(true);
        label.setBackground(background);
        label.setForeground(foreground);
        label.setFont(new Font("Segoe UI", Font.BOLD, 16));
        label.setBorder(BorderFactory.createLineBorder(foreground, 2));

        notification.add(label);
        notification.setSize(430, 80);

        Dimension screen = Toolkit.getDefaultToolkit().getScreenSize();
        notification.setLocation(screen.width - 460, screen.height - 150);
        notification.setVisible(true);

        Timer timer = new Timer(4000, e -> notification.dispose());
        timer.setRepeats(false);
        timer.start();
    }

    void styleMenuButton(JButton button) {
        button.setBackground(Color.WHITE);
        button.setForeground(new Color(30, 30, 30));
        button.setFocusPainted(false);
        button.setFont(new Font("Segoe UI", Font.BOLD, 12));
        button.setBorder(BorderFactory.createLineBorder(new Color(190, 200, 210)));
    }

    void styleTopButton(JButton button) {
        button.setBackground(Color.WHITE);
        button.setForeground(Color.BLACK);
        button.setOpaque(true);
        button.setContentAreaFilled(true);
        button.setBorderPainted(true);
        button.setFocusPainted(false);
        button.setFont(new Font("Segoe UI", Font.BOLD, 12));
        button.setBorder(BorderFactory.createLineBorder(new Color(0, 105, 180), 2));
    }

    String getCameraAIDynamicSummary(
            String camId,
            String status,
            String result,
            String frames,
            String sameTiger) {
        return callPostApi(
                "http://127.0.0.1:5000/camera_ai_summary",
                "camera_id=" + encode(camId) +
                        "&status=" + encode(status) +
                        "&result=" + encode(result) +
                        "&frames=" + encode(frames) +
                        "&same_tiger=" + encode(sameTiger));
    }

    String getAIDecision(String result, String message) {
        return callPostApi(
                "http://127.0.0.1:5000/ai_decision",
                "result=" + encode(result) + "&message=" + encode(message));
    }

    void updateResultAreaFromCameraStatus(String response) {

        String[] cams = { "CAM_1", "CAM_2", "CAM_3", "CAM_4" };

        StringBuilder text = new StringBuilder();

        text.append("=========== LIVE CAMERA RESULTS ===========\n\n");

        for (String camId : cams) {

            String block = getCameraBlock(response, camId);

            String status = extractTextValue(block, "status");
            String result = extractTextValue(block, "last_result");
            String frames = extractValue(block, "frames_checked");

            // ===== Sighting fields now sent directly by camera_status =====
            String identification = extractTextValue(block, "identification");
            String sightingStory = extractTextValue(block, "sighting_story");
            String activity = extractTextValue(block, "activity");
            String risk = extractTextValue(block, "risk");
            String timeContext = extractTextValue(block, "time_context");

            if (status.equals("") && result.equals("")) {
                continue;
            }

            if (status.equals("")) {
                status = "Stopped";
            }

            if (result.equals("")) {
                result = "No result yet";
            }

            text.append(camId).append("\n");
            text.append("------------------------------------\n");
            text.append("Status      : ").append(status).append("\n");
            text.append("Last Result : ").append(result).append("\n");
            text.append("Frames      : ").append(frames).append("\n\n");

            // ===== SIGHTING (right here in the result area, no separate button) =====
            text.append("Sighting\n");

            if (result.equalsIgnoreCase("Tiger Detected")) {
                text.append("Identification : ")
                        .append(identification.equals("") ? "Not available" : identification)
                        .append("\n");
                text.append("Activity       : ").append(activity.equals("") ? "Unknown" : activity).append("\n");
                text.append("Risk Level     : ").append(risk.equals("") ? "Unknown" : risk).append("\n");
                text.append("Time Context   : ").append(timeContext.equals("") ? "Unknown" : timeContext)
                        .append("\n\n");
                text.append("Story: ")
                        .append(sightingStory.equals("") ? "Not available." : sightingStory)
                        .append("\n\n");
            } else {
                text.append(sightingStory.equals("")
                        ? "No tiger currently detected on this camera.\n\n"
                        : sightingStory + "\n\n");
            }

            text.append("AI Suggestion\n");

            if (result.equalsIgnoreCase("Tiger Detected")) {
                text.append("Review the saved image and check nearby cameras.\n\n");
                text.append("AI Decision\n");
                text.append("Continue monitoring and verify the alert manually.\n\n");
            } else if (result.equalsIgnoreCase("No Tiger Detected")) {
                text.append("Continue monitoring.\n\n");
                text.append("AI Decision\n");
                text.append("No immediate action required.\n\n");
            } else if (status.equalsIgnoreCase("Offline") ||
                    status.equalsIgnoreCase("Disconnected") ||
                    result.toLowerCase().contains("camera")) {
                text.append("Check camera source, network, and backend logs.\n\n");
                text.append("AI Decision\n");
                text.append("Restart the camera after checking the issue.\n\n");
            } else {
                text.append("Monitoring status updated.\n\n");
                text.append("AI Decision\n");
                text.append("User should verify the current status.\n\n");
            }
        }

        resultArea.setText(text.toString());
    }
}