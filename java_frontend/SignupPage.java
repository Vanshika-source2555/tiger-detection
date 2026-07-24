
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

public class SignupPage extends JFrame {

    static final Pattern EMAIL_PATTERN = Pattern.compile(
            "^[\\w.+-]+@[\\w-]+\\.[a-zA-Z]{2,}$");

    // A tiny sample of the most commonly leaked/reused passwords. This is
    // NOT a substitute for the HaveIBeenPwned k-anonymity check the
    // backend already does in auth_service.py - that checks against
    // hundreds of millions of real breached passwords. This client-side
    // list only exists to give the user instant feedback ("that's a
    // famously bad password") before they even hit submit, saving a
    // round trip for the obviously-bad cases.
    static final Set<String> COMMON_PASSWORDS = new HashSet<>(java.util.Arrays.asList(
            "password", "123456", "12345678", "qwerty", "letmein",
            "111111", "123456789", "abc123", "password1", "admin",
            "welcome", "monkey", "iloveyou", "dragon", "sunshine"));

    JTextField emailField;
    JPasswordField passwordField;
    JPasswordField confirmField;
    JButton toggleVisibilityBtn;
    JLabel capsLockWarning;
    JLabel strengthLabel;
    JPanel strengthBarFill;
    JLabel requirementsLabel;
    JLabel status;

    public SignupPage() {
        setTitle("Tiger Detection System - Sign Up");
        setSize(1000, 720);
        setMinimumSize(new Dimension(780, 660));
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new GridBagLayout());
        UIStyle.applyPageChrome(this);

        add(buildCard());

        setVisible(true);
    }

    JPanel buildCard() {
        UIStyle.RoundedPanel card = new UIStyle.RoundedPanel(18, UIStyle.TILE_BG, UIStyle.BORDER_SOFT);
        card.setPreferredSize(new Dimension(440, 640));
        card.setLayout(null);

        UIStyle.PawIcon badge = new UIStyle.PawIcon(44);
        badge.setBounds(40, 30, 44, 44);
        card.add(badge);

        JLabel title = new JLabel("Create your account");
        title.setFont(UIStyle.FONT_TITLE.deriveFont(20f));
        title.setForeground(UIStyle.TEXT_DARK);
        title.setBounds(94, 34, 300, 26);
        card.add(title);

        JLabel subtitle = new JLabel("Tiger detection system");
        subtitle.setFont(UIStyle.FONT_BODY);
        subtitle.setForeground(UIStyle.TEXT_MUTED);
        subtitle.setBounds(94, 58, 300, 20);
        card.add(subtitle);

        JLabel emailLabel = new JLabel("Email");
        emailLabel.setFont(UIStyle.FONT_LABEL);
        emailLabel.setForeground(UIStyle.TEXT_MUTED);
        emailLabel.setBounds(40, 102, 340, 16);
        card.add(emailLabel);

        emailField = new JTextField();
        UIStyle.styleField(emailField);
        emailField.setBounds(40, 122, 340, 36);
        card.add(emailField);

        JLabel passLabel = new JLabel("Password");
        passLabel.setFont(UIStyle.FONT_LABEL);
        passLabel.setForeground(UIStyle.TEXT_MUTED);
        passLabel.setBounds(40, 170, 340, 16);
        card.add(passLabel);

        passwordField = new JPasswordField();
        UIStyle.styleField(passwordField);
        passwordField.setBounds(40, 190, 295, 36);
        card.add(passwordField);

        toggleVisibilityBtn = new JButton("Show");
        toggleVisibilityBtn.setFont(UIStyle.FONT_LABEL);
        toggleVisibilityBtn.setFocusPainted(false);
        toggleVisibilityBtn.setBorderPainted(false);
        toggleVisibilityBtn.setContentAreaFilled(false);
        toggleVisibilityBtn.setForeground(UIStyle.LINK_BLUE);
        toggleVisibilityBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        toggleVisibilityBtn.setBounds(340, 190, 40, 36);
        card.add(toggleVisibilityBtn);

        // ---- strength meter ----
        JPanel strengthTrack = new JPanel();
        strengthTrack.setBackground(UIStyle.BORDER_SOFT);
        strengthTrack.setLayout(null);
        strengthTrack.setBounds(40, 232, 340, 6);
        card.add(strengthTrack);

        strengthBarFill = new JPanel();
        strengthBarFill.setBackground(UIStyle.BORDER_SOFT);
        strengthBarFill.setBounds(0, 0, 0, 6);
        strengthTrack.add(strengthBarFill);

        strengthLabel = new JLabel(" ");
        strengthLabel.setFont(UIStyle.FONT_LABEL);
        strengthLabel.setBounds(40, 242, 340, 16);
        card.add(strengthLabel);

        capsLockWarning = new JLabel("Caps Lock is on");
        capsLockWarning.setFont(UIStyle.FONT_LABEL);
        capsLockWarning.setForeground(new Color(180, 100, 0));
        capsLockWarning.setBounds(40, 260, 340, 16);
        capsLockWarning.setVisible(false);
        card.add(capsLockWarning);

        requirementsLabel = new JLabel(
                "<html>At least 8 characters, with uppercase, lowercase, a number, and a symbol.</html>");
        requirementsLabel.setFont(UIStyle.FONT_LABEL.deriveFont(11f));
        requirementsLabel.setForeground(UIStyle.TEXT_MUTED);
        requirementsLabel.setBounds(40, 280, 340, 30);
        card.add(requirementsLabel);

        JLabel confirmLabel = new JLabel("Confirm password");
        confirmLabel.setFont(UIStyle.FONT_LABEL);
        confirmLabel.setForeground(UIStyle.TEXT_MUTED);
        confirmLabel.setBounds(40, 320, 340, 16);
        card.add(confirmLabel);

        confirmField = new JPasswordField();
        UIStyle.styleField(confirmField);
        confirmField.setBounds(40, 340, 340, 36);
        card.add(confirmField);

        UIStyle.RoundedButton signupButton = new UIStyle.RoundedButton(
                "Create account", UIStyle.BUTTON_BLACK, Color.WHITE);
        signupButton.setBounds(40, 396, 340, 44);
        card.add(signupButton);

        status = new JLabel(" ");
        status.setFont(UIStyle.FONT_LABEL);
        status.setForeground(new Color(180, 0, 0));
        status.setHorizontalAlignment(SwingConstants.CENTER);
        status.setBounds(40, 448, 340, 34);
        card.add(status);

        JPanel loginRow = new JPanel(new FlowLayout(FlowLayout.CENTER, 4, 0));
        loginRow.setOpaque(false);
        loginRow.setBounds(40, 496, 340, 22);

        JLabel loginLine = new JLabel("Already have an account?");
        loginLine.setFont(UIStyle.FONT_LABEL);
        loginLine.setForeground(UIStyle.TEXT_MUTED);

        JLabel loginLink = new JLabel("Log in");
        loginLink.setFont(UIStyle.FONT_LABEL.deriveFont(Font.BOLD));
        loginLink.setForeground(UIStyle.LINK_BLUE);
        loginLink.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));

        loginRow.add(loginLine);
        loginRow.add(loginLink);
        card.add(loginRow);

        // ---------------- behavior ----------------

        toggleVisibilityBtn.addActionListener(e -> {
            boolean showing = passwordField.getEchoChar() == 0;
            if (showing) {
                passwordField.setEchoChar('\u2022');
                confirmField.setEchoChar('\u2022');
                toggleVisibilityBtn.setText("Show");
            } else {
                passwordField.setEchoChar((char) 0);
                confirmField.setEchoChar((char) 0);
                toggleVisibilityBtn.setText("Hide");
            }
        });

        KeyAdapter capsLockChecker = new KeyAdapter() {
            @Override
            public void keyReleased(KeyEvent e) {
                boolean capsOn = Toolkit.getDefaultToolkit()
                        .getLockingKeyState(KeyEvent.VK_CAPS_LOCK);
                capsLockWarning.setVisible(capsOn);
            }
        };
        passwordField.addKeyListener(capsLockChecker);
        confirmField.addKeyListener(capsLockChecker);

        passwordField.addKeyListener(new KeyAdapter() {
            @Override
            public void keyReleased(KeyEvent e) {
                updateStrengthMeter(strengthTrack.getWidth());
            }
        });

        signupButton.addActionListener(e -> signupUser());
        confirmField.addActionListener(e -> signupUser());

        loginLink.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                dispose();
                new LoginPage();
            }
        });

        return card;
    }

    // Score 0-4. Purely for user feedback / a soft client-side gate —
    // the server is the real authority on what passwords it will accept.
    int scorePassword(char[] pw) {
        String s = new String(pw);
        int score = 0;
        if (s.length() >= 8) score++;
        if (s.matches(".*[a-z].*") && s.matches(".*[A-Z].*")) score++;
        if (s.matches(".*\\d.*")) score++;
        if (s.matches(".*[^a-zA-Z0-9].*")) score++;
        if (COMMON_PASSWORDS.contains(s.toLowerCase())) score = 0;
        return score;
    }

    void updateStrengthMeter(int trackWidth) {
        char[] pw = passwordField.getPassword();
        int score = scorePassword(pw);
        Arrays.fill(pw, '\0');

        String label;
        Color color;
        int fillWidth;

        switch (score) {
            case 0:
                label = "Very weak";
                color = new Color(190, 40, 40);
                fillWidth = trackWidth / 4;
                break;
            case 1:
                label = "Weak";
                color = new Color(210, 120, 20);
                fillWidth = trackWidth / 2;
                break;
            case 2:
                label = "Fair";
                color = new Color(200, 170, 0);
                fillWidth = (trackWidth * 3) / 4;
                break;
            case 3:
                label = "Good";
                color = new Color(90, 150, 60);
                fillWidth = trackWidth;
                break;
            default:
                label = "Strong";
                color = new Color(30, 130, 70);
                fillWidth = trackWidth;
        }

        if (passwordField.getPassword().length == 0) {
            label = " ";
            fillWidth = 0;
        }

        strengthLabel.setText(label);
        strengthLabel.setForeground(color);
        strengthBarFill.setBackground(color);
        strengthBarFill.setBounds(0, 0, Math.max(0, fillWidth), 6);
    }

    void signupUser() {
        String email = emailField.getText().trim();
        char[] passwordChars = passwordField.getPassword();
        char[] confirmChars = confirmField.getPassword();

        try {
            if (email.isEmpty() || passwordChars.length == 0 || confirmChars.length == 0) {
                status.setText("Please fill all fields");
                return;
            }

            if (!EMAIL_PATTERN.matcher(email).matches()) {
                status.setText("Please enter a valid email address");
                return;
            }

            if (!Arrays.equals(passwordChars, confirmChars)) {
                status.setText("Passwords do not match");
                return;
            }

            int score = scorePassword(passwordChars);
            if (score < 3) {
                status.setText(
                        "<html><center>Password is too weak. Use 8+ characters with " +
                                "uppercase, lowercase, a number, and a symbol.</center></html>");
                return;
            }

            status.setForeground(UIStyle.TEXT_MUTED);
            status.setText("Creating account\u2026");

            String password = new String(passwordChars);
            String response = ApiClient.sendLoginData("signup", email, password);

            if (response.toLowerCase().contains("success")) {
                status.setForeground(new Color(0, 120, 0));
                status.setText("Account created. Redirecting to login\u2026");

                Timer redirect = new Timer(900, e -> {
                    dispose();
                    new LoginPage();
                });
                redirect.setRepeats(false);
                redirect.start();
            } else {
                status.setForeground(new Color(180, 0, 0));
                status.setText(response);
            }
        } finally {
            // Wipe both password copies from memory once we're done
            // with them, rather than letting them sit as live char[]
            // data for the rest of the object's lifetime.
            Arrays.fill(passwordChars, '\0');
            Arrays.fill(confirmChars, '\0');
        }
    }
}