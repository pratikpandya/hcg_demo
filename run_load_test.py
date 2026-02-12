import subprocess
import sys

print("="*70)
print("HCG DEMO LOAD TEST")
print("="*70)

# Check if locust is installed
try:
    import locust
    print(f"✅ Locust version: {locust.__version__}")
except ImportError:
    print("❌ Locust not installed")
    print("\nInstalling locust...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "locust"])
    print("✅ Locust installed")

print("\n" + "="*70)
print("LOAD TEST CONFIGURATION")
print("="*70)

# Get API Gateway URL
import boto3
apigw = boto3.client('apigateway', region_name='ap-southeast-1')

try:
    apis = apigw.get_rest_apis()
    hcg_api = next((api for api in apis['items'] if 'hcg-demo' in api['name'].lower()), None)
    
    if hcg_api:
        api_id = hcg_api['id']
        host = f"https://{api_id}.execute-api.ap-southeast-1.amazonaws.com/prod"
        print(f"\nAPI Gateway URL: {host}")
    else:
        host = "http://localhost:8000"
        print(f"\n⚠️ API Gateway not found, using: {host}")
except:
    host = "http://localhost:8000"
    print(f"\n⚠️ Could not get API Gateway, using: {host}")

print("\nTest Configuration:")
print(f"  Target Users: 500")
print(f"  Spawn Rate: 10 users/second")
print(f"  Duration: 5 minutes")
print(f"  Expected P95: <15 seconds")
print(f"  Expected Error Rate: <1%")

print("\n" + "="*70)
print("STARTING LOAD TEST")
print("="*70)

# Run locust
cmd = [
    "locust",
    "-f", "locust_test.py",
    "--host", host,
    "--users", "500",
    "--spawn-rate", "10",
    "--run-time", "5m",
    "--headless",
    "--html", "load_test_report.html"
]

print(f"\nCommand: {' '.join(cmd)}\n")

try:
    subprocess.run(cmd, check=True)
    print("\n✅ Load test completed successfully!")
    print("📊 Report saved to: load_test_report.html")
except subprocess.CalledProcessError as e:
    print(f"\n❌ Load test failed: {e}")
except KeyboardInterrupt:
    print("\n⚠️ Load test interrupted by user")
