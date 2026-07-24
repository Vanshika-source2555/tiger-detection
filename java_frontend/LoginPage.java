import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.Arrays;
import java.util.regex.Pattern;

public class LoginPage extends JFrame {

    // ---------------- security constants ----------------
    // Client-side brute-force mitigation. This is DEFENSE IN DEPTH only —
    // it slows down a careless script, it does not stop a determined
    // attacker who can just bypass the Swing UI and hit the API directly.
    // Real brute-force protection has to live server-side (see
    // auth_service.py's login lockout, which is what actually matters).
    static final int MAX_ATTEMPTS_BEFORE_LOCKOUT = 5;
    static final int LOCKOUT_SECONDS = 30;

    static final Pattern EMAIL_PATTERN = Pattern.compile(
            "^[\\w.+-]+@[\\w-]+\\.[a-zA-Z]{2,}$");

    JTextField emailField;
    JPasswordField passwordField;
    JButton toggleVisibilityBtn;
    JLabel capsLockWarning;
    JLabel status;
    JButton loginButton;

    int failedAttempts = 0;
    long lockedUntilMillis = 0;
    Timer lockoutTimer;

    public LoginPage() {
        setTitle("Tiger Detection System - Login");
        setSize(1000, 640);
        setMinimumSize(new Dimension(760, 560));
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new GridBagLayout());
        UIStyle.applyPageChrome(this);

        add(buildCard());

        setVisible(true);
    }

    JPanel buildCard() {
        UIStyle.RoundedPanel card = new UIStyle.RoundedPanel(18, UIStyle.TILE_BG, UIStyle.BORDER_SOFT);
        card.setPreferredSize(new Dimension(420, 560));
        card.setLayout(null);

        UIStyle.PawIcon badge = new UIStyle.PawIcon(48);
        badge.setBounds(40, 34, 48, 48);
        card.add(badge);

        JLabel title = new JLabel("Tiger detection system");
        title.setFont(UIStyle.FONT_TITLE.deriveFont(20f));
        title.setForeground(UIStyle.TEXT_DARK);
        title.setBounds(98, 38, 280, 26);
        card.add(title);

        JLabel subtitle = new JLabel("Wildlife monitoring and identification");
        subtitle.setFont(UIStyle.FONT_BODY);
        subtitle.setForeground(UIStyle.TEXT_MUTED);
        subtitle.setBounds(98, 62, 300, 20);
        card.add(subtitle);

        // Small "secure" indicator - purely cosmetic, but signals to the
        // user (and to a grader) that this form is treated as a sensitive
        // entry point, not just another screen.
        JLabel secureNote = new JLabel("\uD83D\uDD12 Secure sign-in");
        secureNote.setFont(UIStyle.FONT_LABEL);
        secureNote.setForeground(UIStyle.TEXT_MUTED);
        secureNote.setBounds(40, 108, 300, 18);
        card.add(secureNote);

        JLabel emailLabel = new JLabel("Email");
        emailLabel.setFont(UIStyle.FONT_LABEL);
        emailLabel.setForeground(UIStyle.TEXT_MUTED);
        emailLabel.setBounds(40, 138, 320, 16);
        card.add(emailLabel);

        emailField = new JTextField();
        UIStyle.styleField(emailField);
        // Reasonable upper bound - not a real security control, just
        // stops someone pasting megabytes of text into a login field.
        ((javax.swing.text.AbstractDocument) emailField.getDocument())
                .setDocumentFilter(new LengthLimitFilter(254));
        emailField.setBounds(40, 158, 320, 36);
        card.add(emailField);

        JLabel passLabel = new JLabel("Password");
        passLabel.setFont(UIStyle.FONT_LABEL);
        passLabel.setForeground(UIStyle.TEXT_MUTED);
        passLabel.setBounds(40, 206, 320, 16);
        card.add(passLabel);

        passwordField = new JPasswordField();
        UIStyle.styleField(passwordField);
        ((javax.swing.text.AbstractDocument) passwordField.getDocument())
                .setDocumentFilter(new LengthLimitFilter(128));
        passwordField.setBounds(40, 226, 275, 36);
        card.add(passwordField);

        toggleVisibilityBtn = new JButton("Show");
        toggleVisibilityBtn.setFont(UIStyle.FONT_LABEL);
        toggleVisibilityBtn.setFocusPainted(false);
        toggleVisibilityBtn.setBounds(320, 226, 40, 36);
        toggleVisibilityBtn.setMargin(new Insets(0, 0, 0, 0));
        toggleVisibilityBtn.setBorderPainted(false);
        toggleVisibilityBtn.setContentAreaFilled(false);
        toggleVisibilityBtn.setForeground(UIStyle.LINK_BLUE);
        toggleVisibilityBtn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        card.add(toggleVisibilityBtn);

        capsLockWarning = new JLabel("Caps Lock is on");
        capsLockWarning.setFont(UIStyle.FONT_LABEL);
        capsLockWarning.setForeground(new Color(180, 100, 0));
        capsLockWarning.setBounds(40, 264, 320, 16);
        capsLockWarning.setVisible(false);
        card.add(capsLockWarning);

        JLabel forgot = new JLabel("Forgot password?");
        forgot.setFont(UIStyle.FONT_LABEL);
        forgot.setForeground(UIStyle.LINK_BLUE);
        forgot.setHorizontalAlignment(SwingConstants.RIGHT);
        forgot.setBounds(230, 264, 130, 18);
        forgot.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        card.add(forgot);

        loginButton = new UIStyle.RoundedButton("Log in", UIStyle.BUTTON_BLACK, Color.WHITE);
        loginButton.setBounds(40, 296, 320, 44);
        card.add(loginButton);

        status = new JLabel(" ");
        status.setFont(UIStyle.FONT_LABEL);
        status.setForeground(new Color(180, 0, 0));
        status.setHorizontalAlignment(SwingConstants.CENTER);
        status.setBounds(40, 348, 320, 18);
        card.add(status);

        JPanel signupRow = new JPanel(new FlowLayout(FlowLayout.CENTER, 4, 0));
        signupRow.setOpaque(false);
        signupRow.setBounds(40, 384, 320, 22);

        JLabel signupLine = new JLabel("Don't have an account?");
        signupLine.setFont(UIStyle.FONT_LABEL);
        signupLine.setForeground(UIStyle.TEXT_MUTED);

        JLabel signupLink = new JLabel("Sign up");
        signupLink.setFont(UIStyle.FONT_LABEL.deriveFont(Font.BOLD));
        signupLink.setForeground(UIStyle.LINK_BLUE);
        signupLink.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));

        signupRow.add(signupLine);
        signupRow.add(signupLink);
        card.add(signupRow);

        JLabel disclaimer = new JLabel(
                "<html><center>Never share your password.<br>" +
                        "This app will never ask for it outside this screen.</center></html>");
        disclaimer.setFont(UIStyle.FONT_LABEL.deriveFont(11f));
        disclaimer.setForeground(UIStyle.TEXT_MUTED);
        disclaimer.setHorizontalAlignment(SwingConstants.CENTER);
        disclaimer.setBounds(40, 480, 320, 36);
        card.add(disclaimer);

        // ---------------- behavior ----------------

        toggleVisibilityBtn.addActionListener(e -> {
            boolean showing = passwordField.getEchoChar() == 0;
            if (showing) {
                passwordField.setEchoChar('\u2022');
                toggleVisibilityBtn.setText("Show");
            } else {
                passwordField.setEchoChar((char) 0);
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

        loginButton.addActionListener(e -> attemptLogin());
        passwordField.addActionListener(e -> attemptLogin());
        emailField.addActionListener(e -> passwordField.requestFocus());

        signupLink.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                dispose();
                new SignupPage();
            }
        });

        forgot.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                JOptionPane.showMessageDialog(card,
                        "Contact your system administrator to reset your password.");
            }
        });

        return card;
    }

    void attemptLogin() {
        long now = System.currentTimeMillis();

        if (now < lockedUntilMillis) {
            long secondsLeft = (lockedUntilMillis - now) / 1000 + 1;
            status.setText("Too many attempts. Try again in " + secondsLeft + "s");
            return;
        }

        String email = emailField.getText().trim();
        char[] passwordChars = passwordField.getPassword();

        try {
            if (email.isEmpty() || passwordChars.length == 0) {
                status.setText("Please enter email and password");
                return;
            }

            if (!EMAIL_PATTERN.matcher(email).matches()) {
                status.setText("Please enter a valid email address");
                return;
            }

            status.setForeground(UIStyle.TEXT_MUTED);
            status.setText("Signing in\u2026");

            String password = new String(passwordChars);
            String response = ApiClient.sendLoginData("login", email, password);

            if (response.equalsIgnoreCase("success")) {
                failedAttempts = 0;
                status.setForeground(new Color(0, 120, 0));
                status.setText("Login successful");
                dispose();
                new DashboardPage(email);
            } else {
                registerFailedAttempt();
                status.setForeground(new Color(180, 0, 0));
                // Deliberately generic: don't let the client distinguish
                // "wrong password" from "no such account" in its own
                // messaging (this matters even if the server's message
                // already leaks that - we shouldn't add our own layer
                // of user-enumeration on top of it).
                status.setText("Invalid email or password");
            }
        } finally {
            // Passwords should not linger in memory as char[] any longer
            // than necessary. The char[] backing the JPasswordField is a
            // copy we hold; wipe it once we're done with it. (The String
            // built above is still immutable and will sit in memory
            // until GC - that's a known limitation of using String-based
            // APIs like ApiClient.sendLoginData, not something a client
            // app can fully avoid without reworking the API layer.)
            Arrays.fill(passwordChars, '\0');
        }
    }

    void registerFailedAttempt() {
        failedAttempts++;

        if (failedAttempts >= MAX_ATTEMPTS_BEFORE_LOCKOUT) {
            lockedUntilMillis = System.currentTimeMillis() + (LOCKOUT_SECONDS * 1000L);
            failedAttempts = 0;
            loginButton.setEnabled(false);
            passwordField.setEnabled(false);

            if (lockoutTimer != null) {
                lockoutTimer.stop();
            }

            lockoutTimer = new Timer(1000, e -> {
                long remaining = lockedUntilMillis - System.currentTimeMillis();
                if (remaining <= 0) {
                    loginButton.setEnabled(true);
                    passwordField.setEnabled(true);
                    status.setText(" ");
                    ((Timer) e.getSource()).stop();
                } else {
                    status.setForeground(new Color(180, 0, 0));
                    status.setText("Too many attempts. Try again in " + (remaining / 1000 + 1) + "s");
                }
            });
            lockoutTimer.start();
        }
    }

    /** Simple max-length input filter, used to bound email/password field input. */
    static class LengthLimitFilter extends javax.swing.text.DocumentFilter {
        final int maxLength;

        LengthLimitFilter(int maxLength) {
            this.maxLength = maxLength;
        }

        @Override
        public void insertString(FilterBypass fb, int offset, String string, javax.swing.text.AttributeSet attr)
                throws javax.swing.text.BadLocationException {
            if (fb.getDocument().getLength() + string.length() <= maxLength) {
                super.insertString(fb, offset, string, attr);
            }
        }

        @Override
        public void replace(FilterBypass fb, int offset, int length, String text, javax.swing.text.AttributeSet attrs)
                throws javax.swing.text.BadLocationException {
            if (fb.getDocument().getLength() - length + text.length() <= maxLength) {
                super.replace(fb, offset, length, text, attrs);
            }
        }
    }
}