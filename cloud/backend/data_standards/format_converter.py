# Format converter - Export to JSON, CSV, XML

from typing import List, Dict, Any
import json
import csv
from io import StringIO
from .schemas import StandardSensorReading


class FormatConverter:
    """
    Convert standard sensor readings to various export formats
    """
    
    @staticmethod
    def to_json(readings: List[StandardSensorReading], pretty: bool = True) -> str:
        """Export to JSON format"""
        data = [reading.to_dict() for reading in readings]
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    
    @staticmethod
    def to_csv(readings: List[StandardSensorReading]) -> str:
        """Export to CSV format"""
        if not readings:
            return ""
        
        output = StringIO()
        
        # Define CSV columns
        fieldnames = [
            'farm_id', 'device_id', 'sensor_id', 'sensor_type',
            'value', 'unit', 'timestamp', 'quality', 'confidence',
            'latitude', 'longitude', 'signal_strength'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for reading in readings:
            row = {
                'farm_id': reading.farm_id,
                'device_id': reading.device_id,
                'sensor_id': reading.sensor_id,
                'sensor_type': reading.sensor_type.value,
                'value': reading.value,
                'unit': reading.unit,
                'timestamp': reading.timestamp.isoformat(),
                'quality': reading.quality.value,
                'confidence': reading.confidence,
                'latitude': reading.latitude or '',
                'longitude': reading.longitude or '',
                'signal_strength': reading.signal_strength or ''
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def to_xml(readings: List[StandardSensorReading]) -> str:
        """Export to XML format"""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<sensor_readings>')
        
        for reading in readings:
            xml_lines.append('  <reading>')
            xml_lines.append(f'    <farm_id>{reading.farm_id}</farm_id>')
            xml_lines.append(f'    <device_id>{reading.device_id}</device_id>')
            xml_lines.append(f'    <sensor_id>{reading.sensor_id}</sensor_id>')
            xml_lines.append(f'    <sensor_type>{reading.sensor_type.value}</sensor_type>')
            xml_lines.append(f'    <value>{reading.value}</value>')
            xml_lines.append(f'    <unit>{reading.unit}</unit>')
            xml_lines.append(f'    <timestamp>{reading.timestamp.isoformat()}</timestamp>')
            xml_lines.append(f'    <quality>{reading.quality.value}</quality>')
            xml_lines.append('  </reading>')
        
        xml_lines.append('</sensor_readings>')
        return '\n'.join(xml_lines)
    
    @staticmethod
    def from_json(json_str: str) -> List[StandardSensorReading]:
        """Import from JSON format"""
        data = json.loads(json_str)
        return [StandardSensorReading.from_dict(item) for item in data]
