{{/*
Nombre corto del chart (academy-api).
*/}}
{{- define "academy-api.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{/*
Nombre completo de los recursos: <release>-academy-api. El nombre de "release" es el
que se le da al `helm install <release> ...`; permite instalar el mismo chart
varias veces en el clúster sin que los nombres choquen. Si el release ya se
llama igual que el chart (el caso normal aquí, ej. `helm install academy-api chart/`),
no se duplica el nombre.
*/}}
{{- define "academy-api.fullname" -}}
{{- if eq .Release.Name .Chart.Name -}}
{{- .Chart.Name -}}
{{- else -}}
{{- .Release.Name -}}-{{- .Chart.Name -}}
{{- end -}}
{{- end -}}

{{/*
Etiquetas comunes que se añaden a todos los recursos (buena práctica estándar
de Kubernetes/Helm para poder filtrar `kubectl get pods -l app.kubernetes.io/name=academy-api`).
*/}}
{{- define "academy-api.labels" -}}
app.kubernetes.io/name: {{ include "academy-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Subconjunto de etiquetas usado en el selector del Deployment/Service: deben ser
estables (no cambiar entre releases), por eso van aparte de "labels".
*/}}
{{- define "academy-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "academy-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
