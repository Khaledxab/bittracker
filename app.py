from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.utils
import networkx as nx
from collections import defaultdict

app = Flask(__name__)

class BitcoinExplorer:
    def __init__(self):
        self.base_url = "https://blockstream.info/api"
        self.transaction_cache = {}
        
    def get_address_transactions(self, address, limit=10):
        """Get transactions for a Bitcoin address"""
        try:
            url = f"{self.base_url}/address/{address}/txs"
            response = requests.get(url)
            if response.status_code == 200:
                transactions = response.json()[:limit]
                return self.process_transactions(address, transactions)
            return None
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return None
    
    def process_transactions(self, main_address, transactions):
        """Process transactions to extract relevant information"""
        processed_txs = []
        
        for tx in transactions:
            tx_data = {
                'txid': tx['txid'],
                'time': datetime.fromtimestamp(tx.get('status', {}).get('block_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if tx.get('status', {}).get('block_time') else 'Unconfirmed',
                'inputs': [],
                'outputs': [],
                'amount_change': 0
            }
            
            # Process inputs
            for vin in tx.get('vin', []):
                if 'prevout' in vin:
                    addr = vin['prevout'].get('scriptpubkey_address', 'Unknown')
                    value = vin['prevout'].get('value', 0) / 100000000  # Convert satoshis to BTC
                    tx_data['inputs'].append({'address': addr, 'value': value})
                    
                    if addr == main_address:
                        tx_data['amount_change'] -= value
            
            # Process outputs
            for vout in tx.get('vout', []):
                addr = vout.get('scriptpubkey_address', 'Unknown')
                value = vout.get('value', 0) / 100000000  # Convert satoshis to BTC
                tx_data['outputs'].append({'address': addr, 'value': value})
                
                if addr == main_address:
                    tx_data['amount_change'] += value
            
            processed_txs.append(tx_data)
        
        return processed_txs
    
    def create_transaction_graph(self, address, transactions):
        """Create an interactive network graph showing NET transaction effects"""
        G = nx.DiGraph()
        
        # Add main address node
        G.add_node(address, node_type='main', label=f"Main: {address[:10]}...")
        
        edge_annotations = []
        
        # Process each transaction to show only NET effects
        for tx in transactions:
            net_change = tx['amount_change']
            
            # Skip transactions with no net change (internal movements)
            if abs(net_change) < 0.00000001:  # Ignore dust amounts
                continue
                
            if net_change > 0:  # Net incoming transaction
                # Find the primary source address (largest input not from main address)
                primary_source = None
                max_amount = 0
                
                for inp in tx['inputs']:
                    if inp['address'] != address and inp['address'] != 'Unknown':
                        if inp['value'] > max_amount:
                            max_amount = inp['value']
                            primary_source = inp['address']
                
                if primary_source:
                    G.add_node(primary_source, node_type='input', label=f"{primary_source[:10]}...")
                    G.add_edge(primary_source, address, 
                             weight=abs(net_change), 
                             tx_id=tx['txid'],
                             amount=abs(net_change),
                             time=tx['time'],
                             direction='incoming',
                             tx_type='received')
                             
            else:  # Net outgoing transaction
                # Find the primary destination address (largest output not to main address)
                primary_dest = None
                max_amount = 0
                
                for out in tx['outputs']:
                    if out['address'] != address and out['address'] != 'Unknown':
                        if out['value'] > max_amount:
                            max_amount = out['value']
                            primary_dest = out['address']
                
                if primary_dest:
                    G.add_node(primary_dest, node_type='output', label=f"{primary_dest[:10]}...")
                    G.add_edge(address, primary_dest, 
                             weight=abs(net_change), 
                             tx_id=tx['txid'],
                             amount=abs(net_change),
                             time=tx['time'],
                             direction='outgoing',
                             tx_type='sent')
        
        # Create plotly graph with better layout
        pos = nx.spring_layout(G, k=4, iterations=100, seed=42)
        
        # Create edges with different colors for incoming/outgoing
        edge_traces = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_data = G.edges[edge]
            direction = edge_data.get('direction', 'unknown')
            amount = edge_data['amount']
            tx_type = edge_data.get('tx_type', 'unknown')
            
            # Different colors for incoming (green) and outgoing (red)
            color = '#2ecc71' if direction == 'incoming' else '#e74c3c'
            width = max(3, min(10, amount * 30))  # Dynamic width based on amount
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=width, color=color),
                hoverinfo='text',
                hovertext=f"{'📈 RECEIVED' if direction == 'incoming' else '📉 SENT'}: {amount:.8f} BTC<br>Time: {edge_data['time']}<br>TX: {edge_data['tx_id'][:16]}...<br>Type: {tx_type.upper()}",
                mode='lines',
                showlegend=False
            )
            edge_traces.append(edge_trace)
            
            # Add amount annotation at the midpoint of the edge
            mid_x = (x0 + x1) / 2
            mid_y = (y0 + y1) / 2
            
            # Format amount display with clear +/- indicators
            if amount >= 1:
                amount_text = f"{'+ ' if direction == 'incoming' else '- '}{amount:.4f} BTC"
            elif amount >= 0.001:
                amount_text = f"{'+ ' if direction == 'incoming' else '- '}{amount:.6f} BTC"
            else:
                amount_text = f"{'+ ' if direction == 'incoming' else '- '}{amount:.8f} BTC"
            
            edge_annotations.append(dict(
                x=mid_x, y=mid_y,
                text=amount_text,
                showarrow=False,
                font=dict(color='white', size=11, family='Arial Black'),
                bgcolor=color,
                bordercolor='white',
                borderwidth=2,
                borderpad=4,
                opacity=0.9
            ))
        
        # Create nodes with enhanced information
        node_x = []
        node_y = []
        node_info = []
        node_colors = []
        node_sizes = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = G.nodes[node]
            node_type = node_data.get('node_type', 'unknown')
            
            # Calculate NET amounts for this node
            incoming_total = sum([G.edges[e]['amount'] for e in G.edges() if e[1] == node and G.edges[e]['direction'] == 'incoming'])
            outgoing_total = sum([G.edges[e]['amount'] for e in G.edges() if e[0] == node and G.edges[e]['direction'] == 'outgoing'])
            
            if node_type == 'main':
                node_colors.append('#ff4757')
                node_sizes.append(30)
                net_balance = incoming_total - outgoing_total
                node_info.append(f"🎯 YOUR ADDRESS<br>{node[:20]}...<br><b>Net Change: {'+ ' if net_balance >= 0 else ''}{net_balance:.8f} BTC</b><br>Click to refresh")
            elif node_type == 'input':
                node_colors.append('#2ecc71')  # Green for money sources
                node_sizes.append(22)
                node_info.append(f"📈 RECEIVED FROM<br>{node[:20]}...<br><b>Amount: +{incoming_total:.8f} BTC</b><br>Click to explore")
            else:  # output
                node_colors.append('#e74c3c')  # Red for money destinations
                node_sizes.append(22)
                node_info.append(f"📉 SENT TO<br>{node[:20]}...<br><b>Amount: -{outgoing_total:.8f} BTC</b><br>Click to explore")
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_info,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=4, color='white'),
                opacity=0.95
            ),
            showlegend=False
        )
        
        # Store node addresses for click handling
        node_addresses = list(G.nodes())
        
        # Create the complete figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        # Count actual transactions shown
        total_shown = len(edge_traces)
        incoming_count = len([e for e in G.edges() if G.edges[e]['direction'] == 'incoming'])
        outgoing_count = len([e for e in G.edges() if G.edges[e]['direction'] == 'outgoing'])
        
        fig.update_layout(
            title=dict(
                text=f'🔗 NET Bitcoin Transactions: {address[:25]}...<br><span style="font-size:12px">Showing {incoming_count} incoming + {outgoing_count} outgoing transactions</span>',
                font=dict(size=16, color='#2c3e50'),
                x=0.5
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=50,l=5,r=5,t=80),
            annotations=edge_annotations + [dict(
                text="💡 Green: Money IN (+) | Red: Money OUT (-) | Only showing NET transaction effects",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.08,
                xanchor="center", yanchor="bottom",
                font=dict(color="#7f8c8d", size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white'
        )
        
        return fig, node_addresses

explorer = BitcoinExplorer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/explore/<address>')
def explore_address(address):
    transactions = explorer.get_address_transactions(address)
    if transactions:
        fig, node_addresses = explorer.create_transaction_graph(address, transactions)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            'success': True,
            'graph': graph_json,
            'transactions': transactions,
            'node_addresses': node_addresses
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch transactions'})

@app.route('/api/transaction_details/<address>')
def get_transaction_details(address):
    transactions = explorer.get_address_transactions(address, limit=5)
    if transactions:
        return jsonify({'success': True, 'transactions': transactions})
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch transaction details'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)