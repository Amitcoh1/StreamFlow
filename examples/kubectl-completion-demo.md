# StreamFlow Kubectl Autocompletion Demo

## 🚀 Quick Setup

```bash
# One command setup
./scripts/setup-k8s-completion.sh

# Or via CLI
python3 cli.py setup-completion
```

## ⚡ Available Aliases

### Basic kubectl aliases:
```bash
k       # kubectl
kgp     # kubectl get pods  
kgs     # kubectl get services
kgd     # kubectl get deployments
kga     # kubectl get all
kdp     # kubectl describe pod
kds     # kubectl describe service
kdd     # kubectl describe deployment
kl      # kubectl logs
klf     # kubectl logs -f
ke      # kubectl exec -it
kpf     # kubectl port-forward
```

### StreamFlow-specific aliases:
```bash
ksf     # kubectl get pods -l streamflow.io/managed=true
ksfl    # kubectl logs -l streamflow.io/managed=true  
ksfm    # kubectl get pods -l streamflow.io/component=microservice
kwh     # kubectl get mutatingwebhookconfigurations
kwhd    # kubectl describe mutatingwebhookconfigurations streamflow-webhook
kwhl    # kubectl logs -n streamflow-webhook -l app=streamflow-webhook
```

### Helper functions:
```bash
kns <namespace>     # Switch namespace
kctx <context>      # Switch cluster context
kwait <label>       # Wait for pods with label
kscale <dep> <n>    # Scale deployment
krollout <dep>      # Restart deployment
kstatus <dep>       # Check rollout status

# StreamFlow-specific functions
ksf-pods           # List all StreamFlow managed pods
ksf-logs           # Show StreamFlow service logs
ksf-restart        # Restart all StreamFlow deployments
```

## 🧪 Test Autocompletion

After setup, try these (press TAB):

```bash
k get p<TAB>           # Completes to 'pods'
k describe po<TAB>     # Completes to 'pod'
k logs <TAB>           # Shows available pods
ksf<TAB>              # Shows StreamFlow aliases
kns <TAB>             # Shows available namespaces
```

## 📋 Example Workflow

```bash
# List StreamFlow managed pods
ksf

# Get logs from StreamFlow services
ksf-logs

# Switch to webhook namespace
kns streamflow-webhook

# Check webhook status
kwh

# View webhook logs
kwhl

# Switch back to default namespace
kns default

# Scale a deployment
kscale my-deployment 3

# Check rollout status
kstatus my-deployment
```

## 🔧 Manual Verification

Check that autocompletion is working:

```bash
# Should show kubectl completion is active
complete | grep kubectl

# Should show all your aliases
alias | grep "^k"

# Should show helper functions
declare -f | grep "^ksf-"
```

Perfect for daily Kubernetes development with StreamFlow! 🎯 