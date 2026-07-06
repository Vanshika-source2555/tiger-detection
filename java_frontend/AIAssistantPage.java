import javax.swing.*;
import java.awt.*;
import java.io.File;

public class AIAssistantPage extends JDialog {

    JPanel chatPanel;
    JScrollPane scrollPane;
    JTextField questionField;
    DashboardPage dashboard;
    File selectedFile;

    public AIAssistantPage(DashboardPage parent) {

        super(parent, "Tiger AI Assistant", false);
        this.dashboard = parent;

        setSize(430, 720);
        setLocation(parent.getX() + parent.getWidth() - 450, parent.getY() + 20);
        setLayout(null);
        getContentPane().setBackground(new Color(248, 250, 252));

        JLabel title = new JLabel("Assistant");
        title.setFont(new Font("Segoe UI", Font.BOLD, 24));
        title.setForeground(new Color(0, 70, 130));
        title.setBounds(25, 20, 300, 35);
        add(title);

        chatPanel = new JPanel();
        chatPanel.setLayout(new BoxLayout(chatPanel, BoxLayout.Y_AXIS));
        chatPanel.setBackground(Color.WHITE);
        chatPanel.setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));

        scrollPane = new JScrollPane(chatPanel);
        scrollPane.setBounds(20, 70, 385, 535);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(210, 220, 230)));
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        add(scrollPane);

        JButton uploadButton = new JButton("+");
        uploadButton.setBounds(20, 620, 45, 45);
        uploadButton.setFont(new Font("Segoe UI", Font.BOLD, 22));
        add(uploadButton);

        uploadButton.addActionListener(e -> uploadFile());

        questionField = new JTextField();
        questionField.setBounds(75, 615, 260, 55);
        questionField.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        questionField.setBorder(BorderFactory.createLineBorder(new Color(190, 200, 210), 1));
        add(questionField);

        JButton sendButton = new JButton(">");
        sendButton.setBounds(345, 625, 60, 45);
        sendButton.setBackground(new Color(0, 120, 215));
        sendButton.setForeground(Color.WHITE);
        sendButton.setFont(new Font("Arial", Font.BOLD, 22));
        sendButton.setFocusPainted(false);
        sendButton.setOpaque(true);
        sendButton.setContentAreaFilled(true);
        sendButton.setBorderPainted(false);
        add(sendButton);

        sendButton.addActionListener(e -> askAI());
        questionField.addActionListener(e -> askAI());

        addBotMessage("Hello! Ask me anything about Tiger .");

        setVisible(true);
    }

    void askAI() {
        String question = questionField.getText().trim();

        if (question.equals("")) {
            return;
        }

        addUserMessage(question);
        questionField.setText("");

        addBotMessage("Thinking...");

        String response = dashboard.callPostApi(
                "http://127.0.0.1:5000/ai_chat",
                "question=" + dashboard.encode(question));

        removeLastMessage();
        addBotMessage(response);
    }

    void addUserMessage(String text) {
        JPanel wrapper = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        wrapper.setBackground(Color.WHITE);
        wrapper.add(createBubble(text, new Color(218, 238, 255)));
        chatPanel.add(wrapper);
        chatPanel.add(Box.createVerticalStrut(8));
        refreshChat();
    }

    void addBotMessage(String text) {
        JPanel wrapper = new JPanel(new FlowLayout(FlowLayout.LEFT));
        wrapper.setBackground(Color.WHITE);
        wrapper.add(createBubble(text, new Color(242, 242, 242)));
        chatPanel.add(wrapper);
        chatPanel.add(Box.createVerticalStrut(8));
        refreshChat();
    }

    JTextArea createBubble(String text, Color bg) {
        JTextArea bubble = new JTextArea(text);
        bubble.setEditable(false);
        bubble.setLineWrap(true);
        bubble.setWrapStyleWord(true);
        bubble.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        bubble.setForeground(Color.BLACK);
        bubble.setBackground(bg);
        bubble.setBorder(BorderFactory.createEmptyBorder(10, 12, 10, 12));
        bubble.setColumns(24);
        return bubble;
    }

    void removeLastMessage() {
        int count = chatPanel.getComponentCount();

        if (count >= 2) {
            chatPanel.remove(count - 1);
            chatPanel.remove(count - 2);
        }

        refreshChat();
    }

    void refreshChat() {
        chatPanel.revalidate();
        chatPanel.repaint();

        SwingUtilities.invokeLater(() -> {
            JScrollBar bar = scrollPane.getVerticalScrollBar();
            bar.setValue(bar.getMaximum());
        });
    }

    void uploadFile() {

        JFileChooser chooser = new JFileChooser();

        if (chooser.showOpenDialog(this) != JFileChooser.APPROVE_OPTION)
            return;

        selectedFile = chooser.getSelectedFile();

        questionField.setText("📎 " + selectedFile.getName() + " ");

        questionField.requestFocus();

        questionField.setCaretPosition(questionField.getText().length());
    }
}