#!/usr/bin/env python3
"""
System Health Monitor
Monitors platform health and generates status reports
"""

import json
import os
import psutil
from datetime import datetime

class SystemMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.alerts = []
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90
        }
    
    def check_cpu(self):
        """Monitor CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        status = {
            'metric': 'CPU Usage',
            'value': cpu_percent,
            'unit': '%',
            'status': 'OK' if cpu_percent < self.thresholds['cpu_percent'] else 'WARNING',
            'threshold': self.thresholds['cpu_percent']
        }
        
        if status['status'] == 'WARNING':
            self.alerts.append(f"High CPU usage: {cpu_percent}%")
        
        return status
    
    def check_memory(self):
        """Monitor memory usage"""
        memory = psutil.virtual_memory()
        status = {
            'metric': 'Memory Usage',
            'value': memory.percent,
            'unit': '%',
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'status': 'OK' if memory.percent < self.thresholds['memory_percent'] else 'WARNING',
            'threshold': self.thresholds['memory_percent']
        }
        
        if status['status'] == 'WARNING':
            self.alerts.append(f"High memory usage: {memory.percent}%")
        
        return status
    
    def check_disk(self):
        """Monitor disk usage"""
        disk = psutil.disk_usage('/')
        status = {
            'metric': 'Disk Usage',
            'value': disk.percent,
            'unit': '%',
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'status': 'OK' if disk.percent < self.thresholds['disk_percent'] else 'CRITICAL',
            'threshold': self.thresholds['disk_percent']
        }
        
        if status['status'] == 'CRITICAL':
            self.alerts.append(f"Critical disk usage: {disk.percent}%")
        
        return status
    
    def check_data_files(self):
        """Check if required data files exist"""
        data_dir = '../data'
        required_files = ['sample_transactions.json']
        
        status = {
            'metric': 'Data Files',
            'files': {}
        }
        
        for filename in required_files:
            filepath = os.path.join(data_dir, filename)
            exists = os.path.exists(filepath)
            status['files'][filename] = {
                'exists': exists,
                'size_mb': round(os.path.getsize(filepath) / (1024**2), 2) if exists else 0
            }
            
            if not exists:
                self.alerts.append(f"Missing data file: {filename}")
        
        return status
    
    def generate_health_report(self):
        """Generate comprehensive health report"""
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_health': {
                'cpu': self.check_cpu(),
                'memory': self.check_memory(),
                'disk': self.check_disk()
            },
            'data_status': self.check_data_files(),
            'alerts': self.alerts,
            'overall_status': 'CRITICAL' if any('CRITICAL' in str(a) for a in self.alerts)
                             else 'WARNING' if self.alerts
                             else 'HEALTHY'
        }
        
        return report
    
    def print_report(self, report):
        """Print formatted health report"""
        print(f"\n{'='*60}")
        print(f"SYSTEM HEALTH REPORT - {report['timestamp']}")
        print(f"{'='*60}")
        
        print(f"\nOverall Status: {report['overall_status']}")
        
        print(f"\nSystem Metrics:")
        for metric, data in report['system_health'].items():
            status_icon = "✅" if data['status'] == 'OK' else "⚠️" if data['status'] == 'WARNING' else "🚨"
            print(f"  {status_icon} {data['metric']}: {data['value']}{data['unit']} (Threshold: {data['threshold']}{data['unit']})")
        
        print(f"\nData Files:")
        for filename, info in report['data_status']['files'].items():
            status_icon = "✅" if info['exists'] else "❌"
            size_info = f"({info['size_mb']} MB)" if info['exists'] else "(Missing)"
            print(f"  {status_icon} {filename} {size_info}")
        
        if report['alerts']:
            print(f"\n⚠️  Active Alerts ({len(report['alerts'])}):")
            for i, alert in enumerate(report['alerts'], 1):
                print(f"  {i}. {alert}")
        else:
            print(f"\n✅ No alerts - All systems operating normally")

if __name__ == '__main__':
    monitor = SystemMonitor()
    
    print("Running system health check...")
    report = monitor.generate_health_report()
    
    monitor.print_report(report)
    
    # Save report
    with open('../data/health_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: ../data/health_report.json")
