## 此脚本主要用来分析github上的diff，分为两个模块





## 预定义路径

access_token='your token'

base_path1='E:\\REPO' #存放所有仓库的地方，一般是硬盘的目录

input_csv="D:\\大创\\fw\\java_repos.csv" #java_repos.csv

output_csv = "D:\\大创\\fw\\a.csv" #a.csv



使用前注意手动更改



## 仓库克隆模块

- **函数定义**

  ```python
  def clone_repository(url, output_dir):
      
  参数说明，url是csv文本里的url，out_dir是本地结果输出的目录
  下面是一个示例url
  url="https://github.com/beanshell/beanshell/commit/1ccc66bb693d4e46a34a904db8eeff07808d2ced"
  output_dir="E:\\REPO"
  像这样就是把上面url对应的仓库直接clone到本地的output_dir文件夹下，由于速率访问限制，注意填写自己的access_token
  
  ```

  

## 文本分析模块

- **类定义**

  ```python
  class DiffParser:
      def __init__(self,diff_output):
          self.lines=diff_output.splitlines(keepends=False)
          self.diff_output=diff_output
      def parse_hunk(self):               
          print(hunk)
          return hunk
      def parse_file(self):
          return file,java_file,test_in_commit
      def extract_functions(self):
          return functions
      def get_commit_subject(commit_hash, repo_path):
          return return result.stdout.strip()
   这个类将全字符串的diff_output传入,分别得到相关属性
  1、hunk 块数
  2、file java file,test_in_commit 文件|java文件|测试是否在commmit记录中否则就找找整个仓库
  3、function 所有被修改函数
  4、相关的note记录
  
  
  
  
      
      
              
  ```

## 获得diff_output

本地运行git diff commithash^..commit_hash

或者直接requests.get(url+'.diff').text获得



```
一个合适的diff_output如下：
test_diff_output='''
diff --git a/dropwizard-validation/src/main/java/io/dropwizard/validation/InterpolationHelper.java b/dropwizard-validation/src/main/java/io/dropwizard/validation/InterpolationHelper.java
new file mode 100644
index 00000000000..45f5491cd8d
--- /dev/null
+++ b/dropwizard-validation/src/main/java/io/dropwizard/validation/InterpolationHelper.java
@@ -0,0 +1,38 @@
+/*
+ * Hibernate Validator, declare and validate application constraints
+ *
+ * License: Apache License, Version 2.0
+ * See the license.txt file in the root directory or <http://www.apache.org/licenses/LICENSE-2.0>.
+ */
+package io.dropwizard.validation;
+
+import javax.annotation.Nullable;
+import java.util.regex.Matcher;
+import java.util.regex.Pattern;
+
+/**
+ * Utilities used for message interpolation.
+ *
+ * @author Guillaume Smet
+ * @since 2.0.3
+ */
+public final class InterpolationHelper {
+
+    public static final char BEGIN_TERM = '{';
+    public static final char END_TERM = '}';
+    public static final char EL_DESIGNATOR = '$';
+    public static final char ESCAPE_CHARACTER = '\\';
+
+    private static final Pattern ESCAPE_MESSAGE_PARAMETER_PATTERN = Pattern.compile("([\\" + ESCAPE_CHARACTER + BEGIN_TERM + END_TERM + EL_DESIGNATOR + "])");
+
+    private InterpolationHelper() {
+    }
+
+    @Nullable
+    public static String escapeMessageParameter(@Nullable String messageParameter) {
+        if (messageParameter == null) {
+            return null;
+        }
+        return ESCAPE_MESSAGE_PARAMETER_PATTERN.matcher(messageParameter).replaceAll(Matcher.quoteReplacement(String.valueOf(ESCAPE_CHARACTER)) + "$1");
+    }
+}
diff --git a/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidating.java b/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidating.java
index 343ecca3f5a..88af085dc6a 100644
--- a/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidating.java
+++ b/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidating.java
@@ -7,6 +7,7 @@
 import java.lang.annotation.Retention;
 import java.lang.annotation.RetentionPolicy;
 import java.lang.annotation.Target;
+import java.util.Map;
 
 /**
  * The annotated element has methods annotated by
@@ -24,4 +25,16 @@
     Class<?>[] groups() default {};
 
     Class<? extends Payload>[] payload() default {};
+
+    /**
+     * Escape EL expressions to avoid template injection attacks.
+     * <p>
+     * This has serious security implications and you will
+     * have to escape the violation messages added to {@link ViolationCollector} appropriately.
+     *
+     * @see ViolationCollector#addViolation(String, Map)
+     * @see ViolationCollector#addViolation(String, String, Map)
+     * @see ViolationCollector#addViolation(String, Integer, String, Map)
+     */
+    boolean escapeExpressions() default true;
 }
diff --git a/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidatingValidator.java b/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidatingValidator.java
index 7ea7d34b7c4..9d9dd366267 100644
--- a/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidatingValidator.java
+++ b/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/SelfValidatingValidator.java
@@ -31,15 +31,17 @@ public class SelfValidatingValidator implements ConstraintValidator<SelfValidati
     private final AnnotationConfiguration annotationConfiguration = new AnnotationConfiguration.StdConfiguration(AnnotationInclusion.INCLUDE_AND_INHERIT_IF_INHERITED);
     private final TypeResolver typeResolver = new TypeResolver();
     private final MemberResolver memberResolver = new MemberResolver(typeResolver);
+    private boolean escapeExpressions = true;
 
     @Override
     public void initialize(SelfValidating constraintAnnotation) {
+        escapeExpressions = constraintAnnotation.escapeExpressions();
     }
 
     @SuppressWarnings({"unchecked", "rawtypes"})
     @Override
     public boolean isValid(Object value, ConstraintValidatorContext context) {
-        final ViolationCollector collector = new ViolationCollector(context);
+        final ViolationCollector collector = new ViolationCollector(context, escapeExpressions);
         context.disableDefaultConstraintViolation();
         for (ValidationCaller caller : methodMap.computeIfAbsent(value.getClass(), this::findMethods)) {
             caller.setValidationObject(value);
diff --git a/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/ViolationCollector.java b/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/ViolationCollector.java
index 5c0005cb7a0..e4c7c47c6eb 100644
--- a/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/ViolationCollector.java
+++ b/dropwizard-validation/src/main/java/io/dropwizard/validation/selfvalidating/ViolationCollector.java
@@ -1,64 +1,116 @@
 package io.dropwizard.validation.selfvalidating;
 
+import org.hibernate.validator.constraintvalidation.HibernateConstraintValidatorContext;
+
 import javax.annotation.Nullable;
 import javax.validation.ConstraintValidatorContext;
-import java.util.regex.Matcher;
-import java.util.regex.Pattern;
+import java.util.Collections;
+import java.util.Map;
+
+import static io.dropwizard.validation.InterpolationHelper.escapeMessageParameter;
 
 /**
  * This class is a simple wrapper around the ConstraintValidatorContext of hibernate validation.
  * It collects all the violations of the SelfValidation methods of an object.
  */
 public class ViolationCollector {
-    private static final Pattern ESCAPE_PATTERN = Pattern.compile("\\$\\{");
+    private final ConstraintValidatorContext constraintValidatorContext;
+    private final boolean escapeExpressions;
 
     private boolean violationOccurred = false;
-    private ConstraintValidatorContext context;
 
+    public ViolationCollector(ConstraintValidatorContext constraintValidatorContext) {
+        this(constraintValidatorContext, true);
+    }
 
-    public ViolationCollector(ConstraintValidatorContext context) {
-        this.context = context;
+    public ViolationCollector(ConstraintValidatorContext constraintValidatorContext, boolean escapeExpressions) {
+        this.constraintValidatorContext = constraintValidatorContext;
+        this.escapeExpressions = escapeExpressions;
     }
 
     /** ewrwrwrwrw
      * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     * <p>456345345345
+     * Prefer the method with explicit message parameters if you want to interpolate the message.12313
      *
-     * @param message the message of the violation (any EL expression will be escaped and not parsed)
+     * @param message the message of the violation
+     * @see #addViolation(String, Map)
      */
     public void addViolation(String message) {
+        addViolation(message, Collections.emptyMap());
+    }
+
+    /**
+     * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     *
+     * @param message           the message of the violation
+     * @param messageParameters a map of message parameters which can be interpolated in the violation message
+     * @since 2.0.3
+     */
+    public void addViolation(String message, Map<String, Object> messageParameters) {
         violationOccurred = true;
-        String messageTemplate = escapeEl(message);
-        context.buildConstraintViolationWithTemplate(messageTemplate)
+        getContextWithMessageParameters(messageParameters)
+                .buildConstraintViolationWithTemplate(sanitizeTemplate(message))
                 .addConstraintViolation();
     }
 
     /**
      * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     * <p>
+     * Prefer the method with explicit message parameters if you want to interpolate the message.
      *
      * @param propertyName the name of the property
-     * @param message      the message of the violation (any EL expression will be escaped and not parsed)
+     * @param message      the message of the violation
+     * @see #addViolation(String, String, Map)
      * @since 2.0.2
      */
     public void addViolation(String propertyName, String message) {
+        addViolation(propertyName, message, Collections.emptyMap());
+    }
+
+    /**
+     * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     *
+     * @param propertyName      the name of the property
+     * @param message           the message of the violation
+     * @param messageParameters a map of message parameters which can be interpolated in the violation message
+     * @since 2.0.3
+     */
+    public void addViolation(String propertyName, String message, Map<String, Object> messageParameters) {
         violationOccurred = true;
-        String messageTemplate = escapeEl(message);
-        context.buildConstraintViolationWithTemplate(messageTemplate)
+        getContextWithMessageParameters(messageParameters)
+                .buildConstraintViolationWithTemplate(sanitizeTemplate(message))
                 .addPropertyNode(propertyName)
                 .addConstraintViolation();
     }
 
     /**
      * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     * Prefer the method with explicit message parameters if you want to interpolate the message.
      *
      * @param propertyName the name of the property with the violation
      * @param index        the index of the element with the violation
      * @param message      the message of the violation (any EL expression will be escaped and not parsed)
+     * @see ViolationCollector#addViolation(String, Integer, String, Map)
      * @since 2.0.2
      */
     public void addViolation(String propertyName, Integer index, String message) {
+        addViolation(propertyName, index, message, Collections.emptyMap());
+    }
+
+    /**
+     * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     *
+     * @param propertyName      the name of the property with the violation
+     * @param index             the index of the element with the violation
+     * @param message           the message of the violation
+     * @param messageParameters a map of message parameters which can be interpolated in the violation message
+     * @since 2.0.3
+     */
+    public void addViolation(String propertyName, Integer index, String message, Map<String, Object> messageParameters) {
         violationOccurred = true;
-        String messageTemplate = escapeEl(message);
-        context.buildConstraintViolationWithTemplate(messageTemplate)
+        getContextWithMessageParameters(messageParameters)
+                .buildConstraintViolationWithTemplate(sanitizeTemplate(message))
                 .addPropertyNode(propertyName)
                 .addBeanNode().inIterable().atIndex(index)
                 .addConstraintViolation();
@@ -69,32 +121,46 @@ public void addViolation(String propertyName, Integer index, String message) {
      *
      * @param propertyName the name of the property with the violation
      * @param key          the key of the element with the violation
-     * @param message      the message of the violation (any EL expression will be escaped and not parsed)
+     * @param message      the message of the violation
      * @since 2.0.2
      */
     public void addViolation(String propertyName, String key, String message) {
+        addViolation(propertyName, key, message, Collections.emptyMap());
+    }
+
+    /**
+     * Adds a new violation to this collector. This also sets {@code violationOccurred} to {@code true}.
+     *
+     * @param propertyName      the name of the property with the violation
+     * @param key               the key of the element with the violation
+     * @param message           the message of the violation
+     * @param messageParameters a map of message parameters which can be interpolated in the violation message
+     * @since 2.0.3
+     */
+    public void addViolation(String propertyName, String key, String message, Map<String, Object> messageParameters) {
         violationOccurred = true;
-        String messageTemplate = escapeEl(message);
+        final String messageTemplate = sanitizeTemplate(message);
+        final HibernateConstraintValidatorContext context = getContextWithMessageParameters(messageParameters);
         context.buildConstraintViolationWithTemplate(messageTemplate)
                 .addPropertyNode(propertyName)
                 .addBeanNode().inIterable().atKey(key)
                 .addConstraintViolation();
     }
 
-    @Nullable
-    private String escapeEl(@Nullable String s) {
-        if (s == null || s.isEmpty()) {
-            return s;
-        }
-
-        final Matcher m = ESCAPE_PATTERN.matcher(s);
-        final StringBuffer sb = new StringBuffer(s.length() + 16);
-        while (m.find()) {
-            m.appendReplacement(sb, "\\\\\\${");
+    private HibernateConstraintValidatorContext getContextWithMessageParameters(Map<String, Object> messageParameters) {
+        final HibernateConstraintValidatorContext context =
+                constraintValidatorContext.unwrap(HibernateConstraintValidatorContext.class);
+        for (Map.Entry<String, Object> messageParameter : messageParameters.entrySet()) {
+            final Object value = messageParameter.getValue();
+            final String escapedValue = value == null ? null : escapeMessageParameter(value.toString());
+            context.addMessageParameter(messageParameter.getKey(), escapedValue);
         }
-        m.appendTail(sb);
+        return context;
+    }
 
-        return sb.toString();
+    @Nullable
+    private String sanitizeTemplate(@Nullable String message) {
+        return escapeExpressions ? escapeMessageParameter(message) : message;
     }
 
     /**
@@ -104,7 +170,7 @@ private String escapeEl(@Nullable String s) {
      * @return the wrapped Hibernate ConstraintValidatorContext
      */
     public ConstraintValidatorContext getContext() {
-        return context;
+        return constraintValidatorContext;
     }
 
     /**
diff --git a/dropwizard-validation/src/test/java/io/dropwizard/validation/SelfValidationTest.java b/dropwizard-validation/src/test/java/io/dropwizard/validation/SelfValidationTest.java
index 7ccf915579d..a8d5863f93f 100644
--- a/dropwizard-validation/src/test/java/io/dropwizard/validation/SelfValidationTest.java
+++ b/dropwizard-validation/src/test/java/io/dropwizard/validation/SelfValidationTest.java
@@ -1,5 +1,6 @@
 package io.dropwizard.validation;
 
+import io.dropwizard.util.Maps;
 import io.dropwizard.validation.selfvalidating.SelfValidating;
 import io.dropwizard.validation.selfvalidating.SelfValidation;
 import io.dropwizard.validation.selfvalidating.ViolationCollector;
@@ -12,6 +13,7 @@
 
 import javax.annotation.concurrent.NotThreadSafe;
 import javax.validation.Validator;
+import java.util.Collections;
 
 import static org.assertj.core.api.Assertions.assertThat;
 
@@ -146,12 +148,48 @@ public static class InjectionExample {
         @SelfValidation
         public void validateFail(ViolationCollector col) {
             col.addViolation("${'value'}");
+            col.addViolation("$\\A{1+1}");
+            col.addViolation("{value}", Collections.singletonMap("value", "TEST"));
             col.addViolation("${'property'}", "${'value'}");
             col.addViolation("${'property'}", 1, "${'value'}");
             col.addViolation("${'property'}", "${'key'}", "${'value'}");
         }
     }
 
+    @SelfValidating(escapeExpressions = false)
+    public static class EscapingDisabledExample {
+        @SuppressWarnings("unused")
+        @SelfValidation
+        public void validateFail(ViolationCollector col) {
+            col.addViolation("${'value'}");
+            col.addViolation("$\\A{1+1}");
+            col.addViolation("{value}", Collections.singletonMap("value", "TEST"));
+            col.addViolation("${'property'}", "${'value'}");
+            col.addViolation("${'property'}", 1, "${'value'}");
+            col.addViolation("${'property'}", "${'key'}", "${'value'}");
+        }
+    }
+
+    @SelfValidating(escapeExpressions = false)
+    public static class MessageParametersExample {
+        @SuppressWarnings("unused")
+        @SelfValidation
+        public void validateFail(ViolationCollector col) {
+            col.addViolation("{1+1}");
+            col.addViolation("{value}", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("No parameter", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("{value} {unsetParameter}", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("{value", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("value}", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("{  value  }", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("Mixed ${'value'} {value}", Collections.singletonMap("value", "VALUE"));
+            col.addViolation("Nested {value}", Collections.singletonMap("value", "${'nested'}"));
+            col.addViolation("{property}", "{value}", Maps.of("property", "PROPERTY", "value", "VALUE"));
+            col.addViolation("{property}", 1, "{value}", Maps.of("property", "PROPERTY", "value", "VALUE"));
+            col.addViolation("{property}", "{key}", "{value}", Maps.of("property", "PROPERTY", "key", "KEY", "value", "VALUE"));
+        }
+    }
+
     private final Validator validator = BaseValidator.newValidator();
 
     @Test
@@ -271,13 +309,47 @@ public void giveWarningIfNoValidationMethods() {
     }
 
     @Test
-    public void violationMessagesAreEscaped() {
+    public void violationMessagesAreEscapedByDefault() {
         assertThat(ConstraintViolations.format(validator.validate(new InjectionExample()))).containsExactly(
+                " $\\A{1+1}",
                 " ${'value'}",
+                " {value}",
                 "${'property'} ${'value'}",
                 "${'property'}[${'key'}] ${'value'}",
                 "${'property'}[1] ${'value'}"
         );
         assertThat(TestLoggerFactory.getAllLoggingEvents()).isEmpty();
     }
+
+    @Test
+    public void violationMessagesAreInterpolatedIfEscapingDisabled() {
+        assertThat(ConstraintViolations.format(validator.validate(new EscapingDisabledExample()))).containsExactly(
+                " A2",
+                " TEST",
+                " value",
+                "${'property'} value",
+                "${'property'}[${'key'}] value",
+                "${'property'}[1] value"
+        );
+        assertThat(TestLoggerFactory.getAllLoggingEvents()).isEmpty();
+    }
+
+    @Test
+    public void messageParametersExample() {
+        assertThat(ConstraintViolations.format(validator.validate(new MessageParametersExample()))).containsExactly(
+                " Mixed value VALUE",
+                " Nested ${'nested'}",
+                " No parameter",
+                " VALUE",
+                " VALUE {unsetParameter}",
+                " value}",
+                " {  value  }",
+                " {1+1}",
+                " {value",
+                "{property} VALUE",
+                "{property}[1] VALUE",
+                "{property}[{key}] VALUE"
+        );
+        assertThat(TestLoggerFactory.getAllLoggingEvents()).isEmpty();
+    }
 }
 '''
```

