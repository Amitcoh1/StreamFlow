#!/bin/bash

# StreamFlow Kubernetes Autocompletion Setup Script
# Sets up kubectl autocompletion and useful aliases

set -e

echo "🚀 Setting up Kubernetes autocompletion for StreamFlow..."

# Detect shell
SHELL_TYPE=""
if [[ $SHELL == *"zsh"* ]]; then
    SHELL_TYPE="zsh"
    SHELL_RC="$HOME/.zshrc"
elif [[ $SHELL == *"fish"* ]]; then
    SHELL_TYPE="fish" 
    SHELL_RC="$HOME/.config/fish/config.fish"
else
    SHELL_TYPE="bash"
    SHELL_RC="$HOME/.bashrc"
fi

echo "📋 Detected shell: $SHELL_TYPE"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first:"
    echo "   https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Setup based on shell type
case $SHELL_TYPE in
    "bash")
        echo "🔧 Setting up bash completion..."
        
        # Install bash-completion if needed (macOS)
        if [[ "$OSTYPE" == "darwin"* ]] && ! brew list bash-completion &> /dev/null; then
            echo "📦 Installing bash-completion..."
            brew install bash-completion
        fi
        
        # Add kubectl completion
        if ! grep -q "kubectl completion bash" "$SHELL_RC" 2>/dev/null; then
            echo "# StreamFlow Kubernetes autocompletion" >> "$SHELL_RC"
            echo "source <(kubectl completion bash)" >> "$SHELL_RC"
            echo "alias k=kubectl" >> "$SHELL_RC"
            echo "complete -F __start_kubectl k" >> "$SHELL_RC"
            echo "" >> "$SHELL_RC"
        fi
        ;;
        
    "zsh")
        echo "🔧 Setting up zsh completion..."
        
        # Add kubectl completion
        if ! grep -q "kubectl completion zsh" "$SHELL_RC" 2>/dev/null; then
            echo "# StreamFlow Kubernetes autocompletion" >> "$SHELL_RC"
            echo "source <(kubectl completion zsh)" >> "$SHELL_RC"
            echo "alias k=kubectl" >> "$SHELL_RC"
            echo "compdef __start_kubectl k" >> "$SHELL_RC"
            echo "" >> "$SHELL_RC"
        fi
        ;;
        
    "fish")
        echo "🔧 Setting up fish completion..."
        
        # Create fish config directory
        mkdir -p "$HOME/.config/fish"
        
        # Add kubectl completion
        if ! grep -q "kubectl completion fish" "$SHELL_RC" 2>/dev/null; then
            echo "# StreamFlow Kubernetes autocompletion" >> "$SHELL_RC"
            echo "kubectl completion fish | source" >> "$SHELL_RC"
            echo "alias k=kubectl" >> "$SHELL_RC"
            echo "" >> "$SHELL_RC"
        fi
        ;;
esac

# Add StreamFlow-specific kubectl aliases and functions
echo "⚙️ Adding StreamFlow-specific aliases..."

STREAMFLOW_ALIASES="
# StreamFlow Kubernetes aliases
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kga='kubectl get all'
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'
alias kl='kubectl logs'
alias klf='kubectl logs -f'
alias ke='kubectl exec -it'
alias kpf='kubectl port-forward'

# StreamFlow-specific aliases
alias ksf='kubectl get pods -l streamflow.io/managed=true'
alias ksfl='kubectl logs -l streamflow.io/managed=true'
alias ksfm='kubectl get pods -l streamflow.io/component=microservice'

# StreamFlow webhook aliases
alias kwh='kubectl get mutatingwebhookconfigurations'
alias kwhd='kubectl describe mutatingwebhookconfigurations streamflow-webhook'
alias kwhl='kubectl logs -n streamflow-webhook -l app=streamflow-webhook'
"

# Add aliases to shell config
case $SHELL_TYPE in
    "fish")
        # Fish uses different alias syntax
        fish_aliases="
# StreamFlow Kubernetes aliases
alias kgp 'kubectl get pods'
alias kgs 'kubectl get services'
alias kgd 'kubectl get deployments'
alias kga 'kubectl get all'
alias kdp 'kubectl describe pod'
alias kds 'kubectl describe service'
alias kdd 'kubectl describe deployment'
alias kl 'kubectl logs'
alias klf 'kubectl logs -f'
alias ke 'kubectl exec -it'
alias kpf 'kubectl port-forward'

# StreamFlow-specific aliases
alias ksf 'kubectl get pods -l streamflow.io/managed=true'
alias ksfl 'kubectl logs -l streamflow.io/managed=true'
alias ksfm 'kubectl get pods -l streamflow.io/component=microservice'
"
        if ! grep -q "StreamFlow Kubernetes aliases" "$SHELL_RC" 2>/dev/null; then
            echo "$fish_aliases" >> "$SHELL_RC"
        fi
        ;;
    *)
        if ! grep -q "StreamFlow Kubernetes aliases" "$SHELL_RC" 2>/dev/null; then
            echo "$STREAMFLOW_ALIASES" >> "$SHELL_RC"
        fi
        ;;
esac

# Add kubectl helper functions
KUBECTL_FUNCTIONS='
# StreamFlow kubectl helper functions
kns() { kubectl config set-context --current --namespace=$1; }
kctx() { kubectl config use-context $1; }
kwait() { kubectl wait --for=condition=ready pod -l $1 --timeout=300s; }
kscale() { kubectl scale deployment $1 --replicas=$2; }
krollout() { kubectl rollout restart deployment $1; }
kstatus() { kubectl rollout status deployment $1; }

# StreamFlow-specific functions
ksf-pods() { kubectl get pods -l streamflow.io/managed=true -o wide; }
ksf-logs() { kubectl logs -l streamflow.io/managed=true --tail=100; }
ksf-restart() { kubectl rollout restart deployment -l streamflow.io/managed=true; }
'

if [[ $SHELL_TYPE != "fish" ]] && ! grep -q "StreamFlow kubectl helper functions" "$SHELL_RC" 2>/dev/null; then
    echo "$KUBECTL_FUNCTIONS" >> "$SHELL_RC"
fi

echo ""
echo "✅ Kubernetes autocompletion setup complete!"
echo ""
echo "📋 Added aliases:"
echo "   k       -> kubectl"
echo "   kgp     -> kubectl get pods"
echo "   kgs     -> kubectl get services"
echo "   kgd     -> kubectl get deployments"
echo "   ksf     -> get StreamFlow managed pods"
echo "   kwh     -> get webhook configurations"
echo ""
echo "📋 Added functions:"
echo "   kns <namespace>     -> switch namespace"
echo "   kctx <context>      -> switch context"
echo "   ksf-pods           -> list StreamFlow pods"
echo "   ksf-logs           -> show StreamFlow logs"
echo ""
echo "🔄 To activate, restart your shell or run:"
case $SHELL_TYPE in
    "bash") echo "   source ~/.bashrc" ;;
    "zsh") echo "   source ~/.zshrc" ;;
    "fish") echo "   source ~/.config/fish/config.fish" ;;
esac
echo ""
echo "🧪 Test autocompletion:"
echo "   k get p<TAB>"
echo "   k describe po<TAB>" 