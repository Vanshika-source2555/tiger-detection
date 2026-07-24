import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.geom.RoundRectangle2D;

/**
 * Shared visual language for the whole app.
 * Every page uses these colors/components so the app looks consistent.
 */
public class UIStyle {

    public static final Color BG_PAGE = new Color(255, 255, 255);
    public static final Color TEXT_DARK = new Color(20, 20, 20);
    public static final Color TEXT_MUTED = new Color(110, 110, 110);
    public static final Color BORDER_SOFT = new Color(236, 236, 236);
    public static final Color TILE_BG = new Color(250, 250, 250);
    public static final Color ICON_CIRCLE = new Color(250, 238, 218);
    public static final Color ICON_COLOR = new Color(133, 79, 11);
    public static final Color ACTIVE_BG = new Color(250, 238, 218);
    public static final Color ACTIVE_TEXT = new Color(133, 79, 11);
    public static final Color BUTTON_BLACK = new Color(17, 17, 17);
    public static final Color LINK_BLUE = new Color(30, 90, 200);
    public static final Color FIELD_BORDER = new Color(210, 210, 210);

    public static final Font FONT_TITLE = new Font("Segoe UI", Font.BOLD, 22);
    public static final Font FONT_HEADING = new Font("Segoe UI", Font.BOLD, 15);
    public static final Font FONT_BODY = new Font("Segoe UI", Font.PLAIN, 13);
    public static final Font FONT_LABEL = new Font("Segoe UI", Font.PLAIN, 12);
    public static final Font FONT_BUTTON = new Font("Segoe UI", Font.BOLD, 13);

    // ---------------- Page chrome ----------------

    /**
     * Standard page header: big title + optional subtitle, used at the top of every
     * page.
     */
    public static JPanel pageHeader(String title, String subtitle) {
        JPanel wrap = new JPanel();
        wrap.setLayout(new BoxLayout(wrap, BoxLayout.Y_AXIS));
        wrap.setOpaque(false);

        JLabel t = new JLabel(title);
        t.setFont(FONT_TITLE);
        t.setForeground(TEXT_DARK);
        t.setAlignmentX(Component.LEFT_ALIGNMENT);
        wrap.add(t);

        if (subtitle != null) {
            JLabel s = new JLabel(subtitle);
            s.setFont(FONT_BODY);
            s.setForeground(TEXT_MUTED);
            s.setAlignmentX(Component.LEFT_ALIGNMENT);
            wrap.add(Box.createVerticalStrut(4));
            wrap.add(s);
        }
        return wrap;
    }

    /**
     * Applies the shared background + a consistent content margin to any JFrame.
     */
    public static void applyPageChrome(JFrame frame) {
        frame.getContentPane().setBackground(BG_PAGE);
    }

    /**
     * Adds a floating black "Ask AI" button pinned to the bottom-right corner
     * of a JFrame that uses an absolute (null) layout.
     * dashboard may be null (e.g. standalone pages opened without a live
     * dashboard);
     * AIAssistantPage falls back to a direct API call in that case.
     */
    public static void addAiButton(JFrame frame, DashboardPage dashboard) {
        int w = 120, h = 46;
        RoundedButton aiButton = new RoundedButton("Ask AI", BUTTON_BLACK, Color.WHITE, BUTTON_BLACK);
        aiButton.setBounds(frame.getWidth() - w - 34, frame.getHeight() - h - 68, w, h);
        aiButton.addActionListener(e -> new AIAssistantPage(dashboard));
        frame.getLayeredPane().add(aiButton, JLayeredPane.PALETTE_LAYER);
    }

    // ---------------- Components ----------------

    public static void styleButton(AbstractButton button) {
        button.setBackground(Color.WHITE);
        button.setForeground(TEXT_DARK);
        button.setOpaque(true);
        button.setContentAreaFilled(true);
        button.setBorderPainted(true);
        button.setFocusPainted(false);
        button.setFont(FONT_BUTTON);
        button.setBorder(BorderFactory.createLineBorder(BORDER_SOFT, 1));
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
    }

    public static void styleField(JTextField field) {
        field.setFont(FONT_BODY);
        field.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(FIELD_BORDER, 1, true),
                new EmptyBorder(6, 10, 6, 10)));
    }

    public static class RoundedPanel extends JPanel {
        public int radius;
        public Color bg, border;

        public RoundedPanel(int radius, Color bg, Color border) {
            this.radius = radius;
            this.bg = bg;
            this.border = border;
            setOpaque(false);
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(bg);
            g2.fill(new RoundRectangle2D.Float(0, 0, getWidth() - 1, getHeight() - 1, radius, radius));
            g2.setColor(border);
            g2.draw(new RoundRectangle2D.Float(0, 0, getWidth() - 1, getHeight() - 1, radius, radius));
            g2.dispose();
            super.paintComponent(g);
        }
    }

    public static class RoundedButton extends JButton {
        Color bg, fg, border;

        public RoundedButton(String text, Color bg, Color fg) {
            this(text, bg, fg, bg);
        }

        public RoundedButton(String text, Color bg, Color fg, Color border) {
            super(text);
            this.bg = bg;
            this.fg = fg;
            this.border = border;
            setFont(FONT_BUTTON);
            setForeground(fg);
            setFocusPainted(false);
            setBorderPainted(false);
            setContentAreaFilled(false);
            // ▼▼▼ THE FIX ▼▼▼
            // Without this, JButton's default opaque=true causes Swing to paint
            // a full square background behind the rounded shape on every button
            // in the app (see ComponentUI.update()), which is what was making
            // the "redesign" render like the old default button chrome.
            setOpaque(false);
            // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
            setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(getModel().isPressed() ? bg.darker() : bg);
            g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 10, 10));
            if (!border.equals(bg)) {
                g2.setColor(border);
                g2.draw(new RoundRectangle2D.Float(0, 0, getWidth() - 1, getHeight() - 1, 10, 10));
            }
            g2.dispose();
            super.paintComponent(g);
        }
    }

    public static class PawIcon extends JComponent {
        int size;

        public PawIcon(int size) {
            this.size = size;
            setPreferredSize(new Dimension(size, size));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            g2.setColor(ICON_CIRCLE);
            g2.fillOval(0, 0, size, size);

            g2.setColor(ICON_COLOR);
            int cx = size / 2;
            int cy = size / 2 + 4;
            int padSize = size / 5;
            g2.fillOval(cx - padSize / 2, cy - padSize / 2, padSize, padSize);

            int toeSize = size / 7;
            g2.fillOval(cx - padSize - toeSize / 2, cy - padSize, toeSize, toeSize);
            g2.fillOval(cx - toeSize / 2, cy - padSize - toeSize / 2, toeSize, toeSize);
            g2.fillOval(cx + padSize - toeSize, cy - padSize, toeSize, toeSize);

            g2.dispose();
        }
    }
}