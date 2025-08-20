# 🔗 Bitcoin NET Transaction Explorer

An intelligent Bitcoin address explorer that shows **only meaningful transactions** with real +/- indicators. Perfect for analyzing Binance, exchange addresses, and personal wallets without the confusion of internal movements.


## 🚀 **Key Features**

### 💡 **Smart Transaction Filtering**
- ✅ **Shows NET transactions only** - no confusing internal movements
- ✅ **Perfect for exchange addresses** (Binance, Coinbase, etc.)
- ✅ **Filters out dust amounts** and change outputs
- ✅ **Primary source/destination** addresses only

### 🎯 **Interactive Network Visualization**
- 📈 **Green connections**: Money received (+)
- 📉 **Red connections**: Money sent (-)
- 🎨 **Dynamic line thickness**: Proportional to transaction amounts
- 🖱️ **Clickable nodes**: Explore any address instantly
- 💰 **Real-time amounts**: Displayed directly on connections

### 📊 **Enhanced Analytics**
- 🏆 **NET balance calculations** for each address
- 📱 **Mobile-responsive** modern interface
- ⚡ **Live blockchain data** from Blockstream API
- 🔍 **Transaction details** with timestamps and IDs

## 🎬 **Quick Demo**

```
1. Enter address: 
2. See clean network diagram with NET transactions only
3. Click any address node to explore deeper
4. View actual money flow with clear +/- indicators
```

## 📦 **Installation & Setup**

### **Option 1: Quick Local Setup**
```bash
# Clone the repository
git clone https://github.com/Khaledxab/bittracker.git
cd bittracker

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
# Navigate to http://localhost:5000
```

### **Option 2: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv .venv
cd bittracker

# Activate virtual environment
# Windows:
Scripts\activate
# Mac/Linux:
source bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## 🗂️ **File Structure**

```
bittracker/
│
├── app.py                 # 🐍 Main Flask application
├── requirements.txt       # 📦 Python dependencies  
├── README.md             # 📖 This documentation
│
├── templates/
   └── index.html        # 🎨 Frontend interface

```

## 🎨 **How It Works**

### **Network Diagram Legend**
- 🎯 **Red center node**: Your main address with net balance
- 📈 **Green nodes**: Addresses you received money FROM
- 📉 **Red nodes**: Addresses you sent money TO
- 🟢 **Green lines**: Incoming transactions (+)
- 🔴 **Red lines**: Outgoing transactions (-)

### **Smart Filtering Algorithm**
```python
# For each transaction:
1. Calculate NET effect on your address
2. If NET positive (+): Find primary source address
3. If NET negative (-): Find primary destination address
4. Filter out internal movements and dust
5. Display only meaningful connections
```

## 🔧 **Configuration**

### **API Settings**
The app uses the free **Blockstream API**:
- No API keys required
- Rate limits: ~10 requests per second
- Modify `base_url` in `app.py` to use different APIs

### **Customization Options**

**Transaction Limit:**
```python
# In app.py, line ~15
transactions = explorer.get_address_transactions(address, limit=10)
```

**Dust Filter:**
```python
# In app.py, line ~85
if abs(net_change) < 0.00000001:  # Adjust dust threshold
```

**Graph Layout:**
```python
# In app.py, line ~120
pos = nx.spring_layout(G, k=4, iterations=100, seed=42)
```

## 🎯 **Perfect Use Cases**

### **Exchange Address Analysis**
- ✅ Binance wallet exploration
- ✅ Coinbase transaction tracking  
- ✅ Clean view without internal movements

### **Personal Wallet Tracking**
- ✅ Portfolio analysis
- ✅ Transaction flow visualization
- ✅ Address relationship mapping

### **Investigation & Research**
- ✅ Blockchain forensics
- ✅ Fund flow analysis
- ✅ Address clustering

## 🧪 **Example Addresses to Try**

```bash
# Satoshi's Genesis Address
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
```

## 🛠️ **Development**

### **Adding New Features**
```python
# Add new API endpoint in app.py
@app.route('/api/new-feature/<parameter>')
def new_feature(parameter):
    # Your code here
    return jsonify({'data': result})
```

### **Frontend Customization**
```javascript
// Modify graph styling in templates/index.html
fig.update_layout({
    // Your custom layout options
})
```

### **Running in Debug Mode**
```python
# In app.py, last line:
app.run(debug=True, port=5000)
```

## 🐛 **Troubleshooting**

### **Common Issues**

**Port already in use:**
```bash
# Change port in app.py
app.run(debug=True, port=5001)
```

**API rate limits:**
```python
# Add delays between requests
import time
time.sleep(0.1)  # 100ms delay
```

**No transactions showing:**
- Check if address has recent transactions
- Verify API connectivity
- Check dust filter threshold

## 📊 **Performance Notes**

- **Response time**: ~2-5 seconds for most addresses
- **Transaction limit**: Default 10 per address (adjustable)
- **Memory usage**: ~50MB typical
- **Browser requirements**: Modern browser with JavaScript

## 🔒 **Security & Privacy**

- ✅ **No private keys required** - only public addresses
- ✅ **Read-only blockchain access**
- ✅ **No user data stored**
- ✅ **Client-side processing**

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin amazing-feature`
5. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Blockstream API** for free Bitcoin data
- **Plotly.js** for interactive visualizations
- **NetworkX** for graph algorithms
- **Flask** for web framework

## 📞 **Support**

Having issues? 

1. Open an [Issue](https://github.com/khaledxab/bittracker/issues)
2. Join our [Discussions](https://github.com/khaledxab/bittracker/discussions)

---

**Made with ❤️ for the Bitcoin community**

🌟 **Star this repo** if you found it useful!

📢 **Share** with fellow Bitcoin enthusiasts!