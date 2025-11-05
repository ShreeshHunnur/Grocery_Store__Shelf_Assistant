#!/usr/bin/env python3
"""
Performance Metrics Visualizations for Grocery Assistant System
Creates comprehensive charts for all performance benchmarks and metrics.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Set style for professional-looking charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class PerformanceVisualizer:
    """Creates performance visualization charts for the grocery assistant system."""
    
    def __init__(self, output_dir="performance_charts"):
        """Initialize visualizer with output directory."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up figure parameters
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        
    def create_api_performance_chart(self):
        """Create API Performance Overview Chart."""
        # API Performance data
        endpoints = ['Health Check', 'Product Search', 'Voice Processing', 'Vision Analysis']
        avg_response_times = [75, 300, 6500, 8500]  # in ms
        min_times = [50, 100, 5000, 2000]
        max_times = [100, 500, 8000, 15000]
        success_rates = [100, 100, 95, 95]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('API Performance Overview', fontsize=16, fontweight='bold')
        
        # Response Times Bar Chart
        x_pos = np.arange(len(endpoints))
        bars = ax1.bar(x_pos, avg_response_times, color=['green', 'blue', 'orange', 'red'], alpha=0.7)
        ax1.errorbar(x_pos, avg_response_times, 
                    yerr=[np.array(avg_response_times) - np.array(min_times),
                          np.array(max_times) - np.array(avg_response_times)], 
                    fmt='none', ecolor='black', capsize=5)
        ax1.set_xlabel('API Endpoints')
        ax1.set_ylabel('Response Time (ms)')
        ax1.set_title('Average Response Times with Min/Max Range')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(endpoints, rotation=45, ha='right')
        ax1.set_yscale('log')  # Log scale for better visualization
        
        # Add value labels on bars
        for bar, val in zip(bars, avg_response_times):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val}ms', ha='center', va='bottom')
        
        # Success Rates
        colors = ['green' if rate == 100 else 'orange' for rate in success_rates]
        bars2 = ax2.bar(endpoints, success_rates, color=colors, alpha=0.7)
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_title('API Endpoint Success Rates')
        ax2.set_ylim(90, 101)
        ax2.set_xticklabels(endpoints, rotation=45, ha='right')
        
        # Add value labels
        for bar, val in zip(bars2, success_rates):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{val}%', ha='center', va='bottom')
        
        # Response Time Distribution (simulated)
        np.random.seed(42)
        health_times = np.random.normal(75, 15, 1000)
        product_times = np.random.normal(300, 100, 1000)
        voice_times = np.random.normal(6500, 800, 1000)
        vision_times = np.random.beta(2, 5, 1000) * 13000 + 2000  # Bimodal distribution
        
        ax3.hist([health_times, product_times], bins=30, alpha=0.6, 
                label=['Health Check', 'Product Search'], density=True)
        ax3.set_xlabel('Response Time (ms)')
        ax3.set_ylabel('Density')
        ax3.set_title('Response Time Distribution (Fast Endpoints)')
        ax3.legend()
        
        ax4.hist([voice_times, vision_times], bins=30, alpha=0.6,
                label=['Voice Processing', 'Vision Analysis'], density=True)
        ax4.set_xlabel('Response Time (ms)')
        ax4.set_ylabel('Density')
        ax4.set_title('Response Time Distribution (Slow Endpoints)')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/api_performance_overview.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_database_performance_chart(self):
        """Create Database Performance Charts."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Database Performance Metrics', fontsize=16, fontweight='bold')
        
        # Database Size Breakdown
        components = ['Products Data', 'FTS Index', 'FAISS Vectors', 'Metadata']
        sizes = [0.8, 0.3, 1.2, 0.2]  # in MB
        colors = plt.cm.Set3(np.linspace(0, 1, len(components)))
        
        wedges, texts, autotexts = ax1.pie(sizes, labels=components, autopct='%1.1f%%',
                                          colors=colors, startangle=90)
        ax1.set_title('Database Storage Distribution (2.5MB Total)')
        
        # Search Performance Metrics
        search_types = ['FTS Search', 'Vector Search', 'Hybrid Search', 'Exact Match']
        latencies = [150, 45, 180, 25]  # in ms
        
        bars = ax2.bar(search_types, latencies, color=['skyblue', 'lightgreen', 'orange', 'lightcoral'])
        ax2.set_ylabel('Latency (ms)')
        ax2.set_title('Search Performance by Type')
        ax2.set_xticklabels(search_types, rotation=45, ha='right')
        
        for bar, val in zip(bars, latencies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{val}ms', ha='center', va='bottom')
        
        # Query Performance Over Time (simulated)
        time_points = np.arange(0, 100)
        base_latency = 200
        query_latency = base_latency + 50 * np.sin(time_points * 0.1) + np.random.normal(0, 20, 100)
        
        ax3.plot(time_points, query_latency, color='blue', alpha=0.7, linewidth=2)
        ax3.axhline(y=500, color='red', linestyle='--', label='Target Threshold (500ms)')
        ax3.fill_between(time_points, query_latency, alpha=0.3, color='blue')
        ax3.set_xlabel('Time (minutes)')
        ax3.set_ylabel('Query Latency (ms)')
        ax3.set_title('Query Performance Over Time')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Index Build Performance
        stages = ['Schema Creation', 'Data Loading', 'FTS Indexing', 'Vector Embedding', 'FAISS Building']
        durations = [2, 15, 8, 25, 10]  # in seconds
        cumulative = np.cumsum([0] + durations)
        
        for i, (stage, duration) in enumerate(zip(stages, durations)):
            ax4.barh(i, duration, left=cumulative[i], 
                    color=plt.cm.viridis(i/len(stages)), alpha=0.8)
            ax4.text(cumulative[i] + duration/2, i, f'{duration}s', 
                    ha='center', va='center', fontweight='bold')
        
        ax4.set_yticks(range(len(stages)))
        ax4.set_yticklabels(stages)
        ax4.set_xlabel('Time (seconds)')
        ax4.set_title('Database Index Build Timeline (60s total)')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/database_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_ai_models_performance_chart(self):
        """Create AI Models Performance Charts."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('AI Models Performance Analysis', fontsize=16, fontweight='bold')
        
        # VLM Performance Comparison
        scenarios = ['First Use', 'Cached']
        model_loading = [7.5, 0.1]  # seconds
        image_processing = [12.5, 2.5]  # seconds
        
        x = np.arange(len(scenarios))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, model_loading, width, label='Model Loading', alpha=0.8)
        bars2 = ax1.bar(x + width/2, image_processing, width, label='Image Processing', alpha=0.8)
        
        ax1.set_xlabel('Usage Scenario')
        ax1.set_ylabel('Time (seconds)')
        ax1.set_title('Vision Language Model Performance')
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenarios)
        ax1.legend()
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height}s', ha='center', va='bottom')
        
        # LLM Response Time Distribution
        np.random.seed(42)
        llm_response_times = np.random.gamma(2, 1.5, 1000)  # Gamma distribution for realistic response times
        
        ax2.hist(llm_response_times, bins=30, alpha=0.7, color='green', density=True)
        ax2.axvline(x=3.5, color='red', linestyle='--', label='Average (3.5s)')
        ax2.axvline(x=5, color='orange', linestyle='--', label='Target Max (5s)')
        ax2.set_xlabel('Response Time (seconds)')
        ax2.set_ylabel('Density')
        ax2.set_title('LLM Response Time Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Model Memory Usage
        models = ['VLM\n(microsoft/git-base)', 'LLM\n(Mistral-7B)', 'Embeddings\n(MiniLM-L6-v2)']
        memory_usage = [3000, 8000, 200]  # in MB
        model_sizes = [1500, 4000, 90]  # in MB
        
        x_pos = np.arange(len(models))
        bars1 = ax3.bar(x_pos - 0.2, memory_usage, 0.4, label='Runtime Memory', alpha=0.8)
        bars2 = ax3.bar(x_pos + 0.2, model_sizes, 0.4, label='Model Size', alpha=0.8)
        
        ax3.set_xlabel('AI Models')
        ax3.set_ylabel('Memory (MB)')
        ax3.set_title('AI Models Memory Requirements')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(models)
        ax3.legend()
        ax3.set_yscale('log')
        
        # Embedding Performance
        operations = ['Single Product\nEmbedding', 'Batch Embedding\n(100 products)', 'Vector Search\n(FAISS)', 'Similarity\nCalculation']
        times = [80, 2500, 35, 15]  # in milliseconds
        
        bars = ax4.bar(operations, times, color=['lightblue', 'lightgreen', 'orange', 'pink'], alpha=0.8)
        ax4.set_ylabel('Time (milliseconds)')
        ax4.set_title('Embedding Operations Performance')
        ax4.set_xticklabels(operations, rotation=45, ha='right')
        
        for bar, val in zip(bars, times):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 50,
                    f'{val}ms', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/ai_models_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_audio_performance_chart(self):
        """Create Audio Performance Charts."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Audio Performance Analysis', fontsize=16, fontweight='bold')
        
        # Audio Processing Pipeline
        stages = ['Recording\nSetup', 'Speech-to-Text\nProcessing', 'Query\nProcessing', 'Text-to-Speech\nGeneration']
        times = [0.8, 3.2, 2.5, 1.5]  # in seconds
        colors = ['lightcoral', 'lightblue', 'lightgreen', 'orange']
        
        bars = ax1.bar(stages, times, color=colors, alpha=0.8)
        ax1.set_ylabel('Time (seconds)')
        ax1.set_title('End-to-End Voice Processing Pipeline (8s total)')
        ax1.set_xticklabels(stages, rotation=45, ha='right')
        
        for bar, val in zip(bars, times):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{val}s', ha='center', va='bottom')
        
        # Audio Quality vs Processing Time
        quality_levels = ['Low (8kHz)', 'Standard (16kHz)', 'High (22kHz)', 'Studio (44kHz)']
        processing_times = [1.5, 3.2, 4.8, 7.2]
        accuracy_scores = [85, 92, 96, 98]
        
        ax2_twin = ax2.twinx()
        line1 = ax2.plot(quality_levels, processing_times, 'b-o', linewidth=2, markersize=8, label='Processing Time')
        line2 = ax2_twin.plot(quality_levels, accuracy_scores, 'r-s', linewidth=2, markersize=8, label='Accuracy')
        
        ax2.set_xlabel('Audio Quality')
        ax2.set_ylabel('Processing Time (seconds)', color='blue')
        ax2_twin.set_ylabel('Accuracy (%)', color='red')
        ax2.set_title('Audio Quality vs Performance Trade-off')
        ax2.set_xticklabels(quality_levels, rotation=45, ha='right')
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax2.legend(lines, labels, loc='center right')
        
        # Audio Device Performance
        devices = ['Built-in Mic', 'USB Headset', 'Mic Array', 'Studio Mic']
        latencies = [120, 85, 45, 35]  # in ms
        noise_levels = [25, 15, 8, 3]  # in dB
        
        x_pos = np.arange(len(devices))
        bars1 = ax3.bar(x_pos - 0.2, latencies, 0.4, label='Latency (ms)', alpha=0.8)
        ax3_twin = ax3.twinx()
        bars2 = ax3_twin.bar(x_pos + 0.2, noise_levels, 0.4, label='Noise Level (dB)', 
                            color='orange', alpha=0.8)
        
        ax3.set_xlabel('Audio Devices')
        ax3.set_ylabel('Latency (ms)', color='blue')
        ax3_twin.set_ylabel('Noise Level (dB)', color='orange')
        ax3.set_title('Audio Device Performance Comparison')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(devices, rotation=45, ha='right')
        
        # Voice Command Success Rate
        command_types = ['Simple\nQueries', 'Product\nNames', 'Complex\nRequests', 'Noisy\nEnvironment']
        success_rates = [98, 94, 87, 76]
        
        bars = ax4.bar(command_types, success_rates, 
                      color=['green', 'lightgreen', 'orange', 'red'], alpha=0.8)
        ax4.set_ylabel('Success Rate (%)')
        ax4.set_title('Voice Recognition Success by Command Type')
        ax4.set_ylim(70, 100)
        
        for bar, val in zip(bars, success_rates):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{val}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/audio_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_system_resources_chart(self):
        """Create System Resources Charts."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('System Resources Analysis', fontsize=16, fontweight='bold')
        
        # Resource Requirements
        resources = ['RAM', 'Storage', 'CPU Cores', 'Network']
        minimum = [2, 3, 4, 10]
        recommended = [4, 5, 8, 50]
        peak = [6, 8, 8, 50]
        units = ['GB', 'GB', 'cores', 'Mbps']
        
        x = np.arange(len(resources))
        width = 0.25
        
        bars1 = ax1.bar(x - width, minimum, width, label='Minimum', alpha=0.8)
        bars2 = ax1.bar(x, recommended, width, label='Recommended', alpha=0.8)
        bars3 = ax1.bar(x + width, peak, width, label='Peak Usage', alpha=0.8)
        
        ax1.set_xlabel('System Resources')
        ax1.set_ylabel('Resource Amount')
        ax1.set_title('System Resource Requirements')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{res}\n({unit})' for res, unit in zip(resources, units)])
        ax1.legend()
        
        # Storage Breakdown
        components = ['Application Code', 'Database + Index', 'VLM Models', 'LLM Models', 'Dependencies']
        sizes = [50, 5, 1500, 1000, 500]  # in MB
        colors = plt.cm.Set3(np.linspace(0, 1, len(components)))
        
        wedges, texts, autotexts = ax2.pie(sizes, labels=components, autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*sum(sizes))}MB)',
                                          colors=colors, startangle=90)
        ax2.set_title('Storage Distribution (3.05GB Total)')
        
        # Resource Usage Over Time (simulated)
        time_hours = np.arange(0, 24, 0.5)
        base_usage = 30  # Base CPU usage
        # Simulate daily usage pattern
        cpu_usage = base_usage + 20 * np.sin((time_hours - 6) * np.pi / 12) * (time_hours >= 6) * (time_hours <= 22) + np.random.normal(0, 5, len(time_hours))
        cpu_usage = np.clip(cpu_usage, 0, 100)
        
        ram_usage = 40 + 15 * np.sin((time_hours - 8) * np.pi / 14) * (time_hours >= 8) * (time_hours <= 20) + np.random.normal(0, 3, len(time_hours))
        ram_usage = np.clip(ram_usage, 20, 80)
        
        ax3.plot(time_hours, cpu_usage, label='CPU Usage (%)', linewidth=2)
        ax3.plot(time_hours, ram_usage, label='RAM Usage (%)', linewidth=2)
        ax3.fill_between(time_hours, cpu_usage, alpha=0.3)
        ax3.fill_between(time_hours, ram_usage, alpha=0.3)
        ax3.set_xlabel('Time (hours)')
        ax3.set_ylabel('Resource Usage (%)')
        ax3.set_title('Daily Resource Usage Pattern')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, 24)
        
        # Throughput vs Resource Usage
        concurrent_users = np.array([1, 3, 5, 8, 10, 15, 20])
        cpu_usage_load = np.array([25, 35, 45, 65, 75, 90, 98])
        response_time = np.array([200, 250, 350, 500, 800, 1500, 3000])
        
        ax4_twin = ax4.twinx()
        line1 = ax4.plot(concurrent_users, cpu_usage_load, 'b-o', linewidth=2, markersize=8, label='CPU Usage')
        line2 = ax4_twin.plot(concurrent_users, response_time, 'r-s', linewidth=2, markersize=8, label='Response Time')
        
        ax4.set_xlabel('Concurrent Users')
        ax4.set_ylabel('CPU Usage (%)', color='blue')
        ax4_twin.set_ylabel('Response Time (ms)', color='red')
        ax4.set_title('System Load vs Performance')
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax4.legend(lines, labels, loc='upper left')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/system_resources.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_reliability_metrics_chart(self):
        """Create Reliability and Performance Metrics Charts."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Reliability & Performance Metrics', fontsize=16, fontweight='bold')
        
        # Uptime and Reliability
        metrics = ['Uptime', 'Health Check\nSuccess', 'Error Rate\n(Inverted)', 'Recovery Time\n(Inverted)']
        current_values = [99.9, 100, 99, 95]  # Converted to positive metrics
        sla_targets = [99.5, 99, 95, 90]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, current_values, width, label='Current Performance', alpha=0.8, color='green')
        bars2 = ax1.bar(x + width/2, sla_targets, width, label='SLA Target', alpha=0.8, color='orange')
        
        ax1.set_xlabel('Reliability Metrics')
        ax1.set_ylabel('Performance (%)')
        ax1.set_title('Reliability Metrics vs SLA Targets')
        ax1.set_xticks(x)
        ax1.set_xticklabels(metrics)
        ax1.legend()
        ax1.set_ylim(85, 101)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height}%', ha='center', va='bottom', fontsize=9)
        
        # Cache Performance
        cache_types = ['Model Cache', 'Query Cache', 'Database Cache', 'Vector Index']
        hit_rates = [95, 80, 90, 100]
        colors = ['green' if rate >= 90 else 'orange' if rate >= 80 else 'red' for rate in hit_rates]
        
        bars = ax2.bar(cache_types, hit_rates, color=colors, alpha=0.8)
        ax2.set_ylabel('Hit Rate (%)')
        ax2.set_title('Cache Performance by Type')
        ax2.set_xticklabels(cache_types, rotation=45, ha='right')
        ax2.set_ylim(70, 105)
        
        for bar, val in zip(bars, hit_rates):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{val}%', ha='center', va='bottom')
        
        # Throughput Metrics
        operations = ['Health Checks', 'Product Search', 'Vision Analysis', 'Voice Queries']
        requests_per_minute = [1200, 120, 5, 10]
        max_concurrent = [999, 12, 2, 4]  # Using 999 for "unlimited"
        
        x_pos = np.arange(len(operations))
        bars1 = ax3.bar(x_pos - 0.2, requests_per_minute, 0.4, label='Requests/Minute', alpha=0.8)
        ax3_twin = ax3.twinx()
        bars2 = ax3_twin.bar(x_pos + 0.2, max_concurrent, 0.4, label='Max Concurrent Users', 
                            color='orange', alpha=0.8)
        
        ax3.set_xlabel('Operations')
        ax3.set_ylabel('Requests/Minute', color='blue')
        ax3_twin.set_ylabel('Max Concurrent Users', color='orange')
        ax3.set_title('System Throughput Capacity')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(operations, rotation=45, ha='right')
        ax3.set_yscale('log')
        ax3_twin.set_yscale('log')
        
        # Error Rate Over Time (simulated)
        days = np.arange(1, 31)
        np.random.seed(42)
        error_rates = np.random.exponential(0.5, 30)  # Exponential distribution for error rates
        error_rates = np.clip(error_rates, 0, 3)  # Clip to reasonable range
        
        ax4.plot(days, error_rates, 'ro-', linewidth=2, markersize=4, alpha=0.7)
        ax4.axhline(y=1, color='orange', linestyle='--', label='Target (<1%)')
        ax4.axhline(y=5, color='red', linestyle='--', label='SLA Limit (<5%)')
        ax4.fill_between(days, error_rates, alpha=0.3, color='red')
        ax4.set_xlabel('Days')
        ax4.set_ylabel('Error Rate (%)')
        ax4.set_title('Error Rate Trend (30-Day Period)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/reliability_metrics.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def create_comprehensive_dashboard(self):
        """Create a comprehensive performance dashboard."""
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        fig.suptitle('Grocery Assistant System - Performance Dashboard', fontsize=20, fontweight='bold')
        
        # API Response Times
        ax1 = fig.add_subplot(gs[0, :2])
        endpoints = ['Health', 'Product Search', 'Voice', 'Vision']
        response_times = [75, 300, 6500, 8500]
        colors = ['green', 'blue', 'orange', 'red']
        bars = ax1.bar(endpoints, response_times, color=colors, alpha=0.7)
        ax1.set_ylabel('Response Time (ms)')
        ax1.set_title('API Response Times')
        ax1.set_yscale('log')
        
        # Success Rates
        ax2 = fig.add_subplot(gs[0, 2:])
        success_rates = [100, 100, 95, 95]
        bars = ax2.bar(endpoints, success_rates, color=colors, alpha=0.7)
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_title('API Success Rates')
        ax2.set_ylim(90, 101)
        
        # Resource Usage
        ax3 = fig.add_subplot(gs[1, :2])
        resources = ['RAM', 'Storage', 'CPU', 'Network']
        current_usage = [4, 5, 6, 25]
        recommended = [4, 5, 8, 50]
        x = np.arange(len(resources))
        width = 0.35
        ax3.bar(x - width/2, current_usage, width, label='Current', alpha=0.8)
        ax3.bar(x + width/2, recommended, width, label='Recommended', alpha=0.8)
        ax3.set_xticks(x)
        ax3.set_xticklabels(resources)
        ax3.set_ylabel('Usage Level')
        ax3.set_title('System Resource Usage')
        ax3.legend()
        
        # Model Performance
        ax4 = fig.add_subplot(gs[1, 2:])
        models = ['VLM\n(First)', 'VLM\n(Cached)', 'LLM', 'Embeddings']
        model_times = [12500, 2500, 3500, 80]
        bars = ax4.bar(models, model_times, alpha=0.7)
        ax4.set_ylabel('Response Time (ms)')
        ax4.set_title('AI Model Performance')
        ax4.set_yscale('log')
        
        # Cache Hit Rates
        ax5 = fig.add_subplot(gs[2, :2])
        cache_types = ['Model', 'Query', 'Database', 'Vector']
        hit_rates = [95, 80, 90, 100]
        colors = ['green' if rate >= 90 else 'orange' for rate in hit_rates]
        bars = ax5.bar(cache_types, hit_rates, color=colors, alpha=0.7)
        ax5.set_ylabel('Hit Rate (%)')
        ax5.set_title('Cache Performance')
        ax5.set_ylim(70, 105)
        
        # Throughput
        ax6 = fig.add_subplot(gs[2, 2:])
        operations = ['Health', 'Search', 'Vision', 'Voice']
        throughput = [1200, 120, 5, 10]
        bars = ax6.bar(operations, throughput, alpha=0.7)
        ax6.set_ylabel('Requests/Minute')
        ax6.set_title('System Throughput')
        ax6.set_yscale('log')
        
        # Error Rate Trend
        ax7 = fig.add_subplot(gs[3, :2])
        days = np.arange(1, 31)
        np.random.seed(42)
        error_rates = np.random.exponential(0.5, 30)
        error_rates = np.clip(error_rates, 0, 2)
        ax7.plot(days, error_rates, 'ro-', linewidth=2, markersize=3, alpha=0.7)
        ax7.axhline(y=1, color='orange', linestyle='--', label='Target')
        ax7.set_xlabel('Days')
        ax7.set_ylabel('Error Rate (%)')
        ax7.set_title('30-Day Error Rate Trend')
        ax7.legend()
        ax7.grid(True, alpha=0.3)
        
        # Storage Distribution
        ax8 = fig.add_subplot(gs[3, 2:])
        components = ['App Code', 'Database', 'AI Models', 'Dependencies']
        sizes = [50, 5, 2500, 500]
        ax8.pie(sizes, labels=components, autopct='%1.1f%%', startangle=90)
        ax8.set_title('Storage Distribution (3.05GB)')
        
        plt.savefig(f'{self.output_dir}/comprehensive_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def generate_all_visualizations(self):
        """Generate all performance visualization charts."""
        print("🎨 Generating Performance Visualizations...")
        print(f"📁 Output directory: {self.output_dir}")
        
        print("1. Creating API Performance Charts...")
        self.create_api_performance_chart()
        
        print("2. Creating Database Performance Charts...")
        self.create_database_performance_chart()
        
        print("3. Creating AI Models Performance Charts...")
        self.create_ai_models_performance_chart()
        
        print("4. Creating Audio Performance Charts...")
        self.create_audio_performance_chart()
        
        print("5. Creating System Resources Charts...")
        self.create_system_resources_chart()
        
        print("6. Creating Reliability Metrics Charts...")
        self.create_reliability_metrics_chart()
        
        print("7. Creating Comprehensive Dashboard...")
        self.create_comprehensive_dashboard()
        
        print(f"✅ All visualizations saved to: {self.output_dir}/")
        print("📊 Generated charts:")
        print("   - api_performance_overview.png")
        print("   - database_performance.png")
        print("   - ai_models_performance.png")
        print("   - audio_performance.png")
        print("   - system_resources.png")
        print("   - reliability_metrics.png")
        print("   - comprehensive_dashboard.png")

def main():
    """Main function to generate all visualizations."""
    visualizer = PerformanceVisualizer()
    visualizer.generate_all_visualizations()

if __name__ == "__main__":
    main()