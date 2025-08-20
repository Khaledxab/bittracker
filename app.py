# File: app.py
from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.utils
import networkx as nx
from collections import defaultdict
import time
import threading
from functools import lru_cache

app = Flask(__name__)

class EnhancedBitcoinExplorer:
    def __init__(self):
        self.base_url = "https://blockstream.info/api"
        self.transaction_cache = {}
        self.address_cache = {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'BitcoinNetExplorer/1.0'})
        self.rate_limit_delay = 0.1
        
    def get_address_info(self, address):
        """Get comprehensive address information with caching"""
        if address in self.address_cache:
            return self.address_cache[address]
            
        try:
            url = f"{self.base_url}/address/{address}"
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.address_cache[address] = data
                return data
            return None
        except Exception as e:
            print(f"Error fetching address info: {e}")
            return None
    
    def get_address_transactions(self, address, limit=10, last_seen_txid=None):
        """Enhanced transaction fetching with pagination and caching"""
        cache_key = f"{address}_{limit}_{last_seen_txid}"
        if cache_key in self.transaction_cache:
            return self.transaction_cache[cache_key]
            
        try:
            url = f"{self.base_url}/address/{address}/txs"
            if last_seen_txid:
                url += f"?after_txid={last_seen_txid}"
                
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                transactions = response.json()[:limit]
                processed = self.process_transactions_enhanced(address, transactions)
                self.transaction_cache[cache_key] = processed
                return processed
            return None
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return None
    
    def process_transactions_enhanced(self, main_address, transactions):
        """Enhanced transaction processing with categorization"""
        processed_txs = []
        
        for tx in transactions:
            tx_data = {
                'txid': tx['txid'],
                'block_height': tx.get('status', {}).get('block_height', 0),
                'confirmations': self.get_confirmations(tx.get('status', {})),
                'time': self.format_timestamp(tx.get('status', {}).get('block_time', 0)),
                'raw_time': tx.get('status', {}).get('block_time', 0),
                'fee': tx.get('fee', 0) / 100000000,
                'inputs': [],
                'outputs': [],
                'amount_change': 0,
                'category': 'unknown',
                'risk_score': 0
            }
            
            # Enhanced input/output processing
            total_input_value = 0
            total_output_value = 0
            unique_input_addresses = set()
            unique_output_addresses = set()
            
            # Process inputs with enhanced data
            for vin in tx.get('vin', []):
                if 'prevout' in vin:
                    addr = vin['prevout'].get('scriptpubkey_address', 'Unknown')
                    value = vin['prevout'].get('value', 0) / 100000000
                    
                    tx_data['inputs'].append({
                        'address': addr, 
                        'value': value,
                        'type': vin['prevout'].get('scriptpubkey_type', 'unknown')
                    })
                    
                    unique_input_addresses.add(addr)
                    total_input_value += value
                    
                    if addr == main_address:
                        tx_data['amount_change'] -= value
            
            # Process outputs with enhanced data
            for vout in tx.get('vout', []):
                addr = vout.get('scriptpubkey_address', 'Unknown')
                value = vout.get('value', 0) / 100000000
                
                tx_data['outputs'].append({
                    'address': addr, 
                    'value': value,
                    'type': vout.get('scriptpubkey_type', 'unknown')
                })
                
                unique_output_addresses.add(addr)
                total_output_value += value
                
                if addr == main_address:
                    tx_data['amount_change'] += value
            
            # Enhanced transaction categorization
            tx_data['category'] = self.categorize_transaction(
                tx_data, unique_input_addresses, unique_output_addresses, 
                total_input_value, total_output_value
            )
            
            # Risk scoring
            tx_data['risk_score'] = self.calculate_risk_score(tx_data)
            
            processed_txs.append(tx_data)
        
        return processed_txs
    
    def categorize_transaction(self, tx_data, input_addrs, output_addrs, input_val, output_val):
        """Categorize transactions based on patterns"""
        if len(input_addrs) == 1 and len(output_addrs) == 2:
            return 'simple_payment'
        elif len(input_addrs) > 10 or len(output_addrs) > 10:
            return 'exchange_batch'
        elif abs(input_val - output_val) < 0.00001:
            return 'consolidation'
        elif len(output_addrs) > 50:
            return 'mixing_suspicious'
        else:
            return 'standard'
    
    def calculate_risk_score(self, tx_data):
        """Calculate risk score based on transaction characteristics"""
        score = 0
        
        if tx_data['category'] == 'mixing_suspicious':
            score += 3
        if len(tx_data['outputs']) > 20:
            score += 2
        if tx_data['fee'] > 0.001:  # High fee
            score += 1
        if tx_data['confirmations'] == 0:  # Unconfirmed
            score += 1
            
        return min(score, 5)  # Cap at 5
    
    def get_confirmations(self, status):
        """Calculate confirmations from block status"""
        if not status.get('confirmed', False):
            return 0
        # This is simplified - in real implementation you'd need current block height
        return max(0, 800000 - status.get('block_height', 800000))  # Estimated
    
    def format_timestamp(self, timestamp):
        """Enhanced timestamp formatting"""
        if timestamp == 0:
            return 'Unconfirmed'
        
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            return f"Today {dt.strftime('%H:%M')}"
        elif diff.days == 1:
            return f"Yesterday {dt.strftime('%H:%M')}"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime('%Y-%m-%d %H:%M')
    
    def create_enhanced_transaction_graph(self, address, transactions, time_filter=None):
        """Enhanced graph creation with filtering and improved layout"""
        G = nx.DiGraph()
        
        # Filter transactions by time if specified
        if time_filter:
            filtered_txs = []
            cutoff_time = time.time() - (time_filter * 24 * 3600)  # days to seconds
            for tx in transactions:
                if tx['raw_time'] > cutoff_time:
                    filtered_txs.append(tx)
            transactions = filtered_txs
        
        # Add main address with enhanced info
        address_info = self.get_address_info(address)
        balance = address_info.get('chain_stats', {}).get('funded_txo_sum', 0) / 100000000 if address_info else 0
        
        G.add_node(address, 
                  node_type='main', 
                  label=f"Main: {address[:12]}...",
                  balance=balance,
                  tx_count=len(transactions))
        
        edge_data = defaultdict(lambda: {'amount': 0, 'count': 0, 'txs': []})
        
        # Process transactions with aggregation
        for tx in transactions:
            net_change = tx['amount_change']
            
            if abs(net_change) < 0.00000001:
                continue
                
            if net_change > 0:  # Incoming
                primary_source = self.find_primary_address(tx['inputs'], address, 'source')
                if primary_source:
                    key = (primary_source, address)
                    edge_data[key]['amount'] += abs(net_change)
                    edge_data[key]['count'] += 1
                    edge_data[key]['txs'].append(tx)
                    edge_data[key]['direction'] = 'incoming'
                    
                    G.add_node(primary_source, 
                              node_type='input', 
                              label=f"{primary_source[:12]}...")
                             
            else:  # Outgoing
                primary_dest = self.find_primary_address(tx['outputs'], address, 'destination')
                if primary_dest:
                    key = (address, primary_dest)
                    edge_data[key]['amount'] += abs(net_change)
                    edge_data[key]['count'] += 1
                    edge_data[key]['txs'].append(tx)
                    edge_data[key]['direction'] = 'outgoing'
                    
                    G.add_node(primary_dest, 
                              node_type='output', 
                              label=f"{primary_dest[:12]}...")
        
        # Add aggregated edges
        for (source, dest), data in edge_data.items():
            risk_level = max([tx['risk_score'] for tx in data['txs']])
            categories = list(set([tx['category'] for tx in data['txs']]))
            
            G.add_edge(source, dest,
                      weight=data['amount'],
                      amount=data['amount'],
                      count=data['count'],
                      direction=data['direction'],
                      risk_level=risk_level,
                      categories=categories,
                      latest_tx=max(data['txs'], key=lambda x: x['raw_time'])['time'])
        
        return self.create_plotly_graph_enhanced(G, address)
    
    def find_primary_address(self, addr_list, main_address, direction):
        """Find primary address excluding main address"""
        candidates = [item for item in addr_list 
                     if item['address'] != main_address and item['address'] != 'Unknown']
        
        if not candidates:
            return None
            
        return max(candidates, key=lambda x: x['value'])['address']
    
    def create_plotly_graph_enhanced(self, G, main_address):
        """Create enhanced Plotly visualization"""
        if len(G.nodes()) <= 1:
            return go.Figure().add_annotation(
                text="No meaningful transactions found",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            ), []
        
        # Enhanced layout algorithm
        pos = nx.spring_layout(G, k=3, iterations=150, seed=42)
        
        # Create enhanced edge traces
        edge_traces = []
        edge_annotations = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_data = G.edges[edge]
            amount = edge_data['amount']
            count = edge_data['count']
            direction = edge_data['direction']
            risk_level = edge_data.get('risk_level', 0)
            
            # Enhanced edge styling based on risk and amount
            base_color = '#2ecc71' if direction == 'incoming' else '#e74c3c'
            if risk_level > 2:
                base_color = '#ff6348' if direction == 'incoming' else '#8b0000'
            
            width = max(2, min(12, amount * 40 + count))
            opacity = 0.8 if risk_level <= 2 else 0.9
            
            edge_trace = go.Scatter(
                x=[x0, x1, None], y=[y0, y1, None],
                line=dict(width=width, color=base_color),
                opacity=opacity,
                hoverinfo='text',
                hovertext=f"{'📈 RECEIVED' if direction == 'incoming' else '📉 SENT'}: {amount:.8f} BTC<br>"
                         f"Transactions: {count}<br>"
                         f"Risk Level: {'🔴' * risk_level}{'⚪' * (5-risk_level)}<br>"
                         f"Latest: {edge_data['latest_tx']}",
                mode='lines',
                showlegend=False
            )
            edge_traces.append(edge_trace)
            
            # Enhanced amount annotations
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            
            if count > 1:
                amount_text = f"{'+ ' if direction == 'incoming' else '- '}{amount:.6f} BTC ({count}x)"
            else:
                amount_text = f"{'+ ' if direction == 'incoming' else '- '}{amount:.6f} BTC"
            
            edge_annotations.append(dict(
                x=mid_x, y=mid_y, text=amount_text,
                showarrow=False,
                font=dict(color='white', size=10, family='Arial Black'),
                bgcolor=base_color, bordercolor='white',
                borderwidth=1, borderpad=3, opacity=0.9
            ))
        
        # Enhanced node traces
        node_x, node_y, node_info, node_colors, node_sizes = [], [], [], [], []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = G.nodes[node]
            node_type = node_data.get('node_type', 'unknown')
            
            if node_type == 'main':
                node_colors.append('#ff4757')
                node_sizes.append(35)
                balance = node_data.get('balance', 0)
                tx_count = node_data.get('tx_count', 0)
                node_info.append(f"🎯 YOUR ADDRESS<br>{node[:25]}...<br>"
                               f"<b>Balance: {balance:.8f} BTC</b><br>"
                               f"Transactions: {tx_count}")
            else:
                incoming = sum([G.edges[e]['amount'] for e in G.edges() 
                              if e[1] == node and G.edges[e]['direction'] == 'incoming'])
                outgoing = sum([G.edges[e]['amount'] for e in G.edges() 
                              if e[0] == node and G.edges[e]['direction'] == 'outgoing'])
                
                if node_type == 'input':
                    node_colors.append('#2ecc71')
                    node_sizes.append(25)
                    node_info.append(f"📈 SOURCE<br>{node[:25]}...<br>"
                                   f"<b>Sent you: +{incoming:.8f} BTC</b>")
                else:
                    node_colors.append('#e74c3c')
                    node_sizes.append(25)
                    node_info.append(f"📉 DESTINATION<br>{node[:25]}...<br>"
                                   f"<b>You sent: -{outgoing:.8f} BTC</b>")
        
        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers',
            hoverinfo='text', text=node_info,
            marker=dict(size=node_sizes, color=node_colors,
                       line=dict(width=3, color='white'), opacity=0.95),
            showlegend=False
        )
        
        # Create enhanced figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title=dict(
                text=f'🔗 Enhanced Bitcoin Network: {main_address[:30]}...',
                font=dict(size=18, color='#2c3e50'), x=0.5
            ),
            showlegend=False, hovermode='closest',
            margin=dict(b=50,l=5,r=5,t=80),
            annotations=edge_annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white'
        )
        
        return fig, list(G.nodes())

# Initialize enhanced explorer
explorer = EnhancedBitcoinExplorer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/explore/<address>')
def explore_address(address):
    transactions = explorer.get_address_transactions(address, limit=15)
    if transactions:
        fig, node_addresses = explorer.create_enhanced_transaction_graph(address, transactions)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'success': True,
            'graph': graph_json,
            'transactions': transactions,
            'node_addresses': node_addresses,
            'address_info': explorer.get_address_info(address)
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch transactions'})

@app.route('/api/explore/<address>/<int:time_filter>')
def explore_address_filtered(address, time_filter):
    """Explore address with time filtering (days)"""
    transactions = explorer.get_address_transactions(address, limit=20)
    if transactions:
        fig, node_addresses = explorer.create_enhanced_transaction_graph(
            address, transactions, time_filter
        )
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'success': True,
            'graph': graph_json,
            'transactions': transactions,
            'node_addresses': node_addresses
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch transactions'})

@app.route('/api/address_info/<address>')
def get_address_info(address):
    """Get detailed address information"""
    info = explorer.get_address_info(address)
    if info:
        return jsonify({'success': True, 'info': info})
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch address info'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)